"""Setup, entity and config flow tests with the fridge mocked out."""

from unittest.mock import AsyncMock, patch

from bleak.backends.device import BLEDevice
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import SOURCE_BLUETOOTH
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.arb_zero.const import DOMAIN
from custom_components.arb_zero.protocol import Setting, parse_status

ADDRESS = "AA:BB:CC:DD:EE:FF"
STATUS = parse_status(bytes.fromhex("aac1f2a00305f9f800000a0d0000000e"))


def _info():
    return BluetoothServiceInfoBleak(
        name="ARBZERO",
        address=ADDRESS,
        rssi=-60,
        manufacturer_data={18513: bytes.fromhex("aabbccddeeff")},
        service_data={},
        service_uuids=["0000fff0-0000-1000-8000-00805f9b34fb"],
        source="local",
        device=BLEDevice(ADDRESS, "ARBZERO", None),
        advertisement=None,
        connectable=True,
        time=0,
        tx_power=None,
    )


async def test_bluetooth_discovery(hass):
    with patch(
        "custom_components.arb_zero.async_setup_entry", return_value=True
    ), patch("custom_components.arb_zero.async_unload_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=_info()
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "bluetooth_confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ADDRESS: ADDRESS}
    assert result["title"] == "ARB Zero EE:FF"


async def test_setup_and_entities(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS},
                            title="ARB Zero EE:FF")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.arb_zero.device.ArbZeroDevice.async_get_status",
        AsyncMock(return_value=STATUS),
    ), patch(
        "custom_components.arb_zero.device.ArbZeroDevice.async_set", AsyncMock()
    ) as mock_set, patch(
        "custom_components.arb_zero.device.ArbZeroDevice.async_disconnect", AsyncMock()
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        states = {s.entity_id: s for s in hass.states.async_all()}
        for eid, s in sorted(states.items()):
            print(eid, s.state, s.attributes.get("unit_of_measurement"))

        temp = states["sensor.arb_zero_ee_ff_temperature"]
        assert float(temp.state) < 0
        assert states["switch.arb_zero_ee_ff_boost"].state == "on"
        assert states["select.arb_zero_ee_ff_battery_protection"].state == "low"
        assert states["select.arb_zero_ee_ff_display_unit"].state == "fahrenheit"
        assert "number.arb_zero_ee_ff_setpoint" in states

        await hass.services.async_call("switch", "turn_off",
            {"entity_id": "switch.arb_zero_ee_ff_boost"}, blocking=True)
        mock_set.assert_awaited_with(Setting.BOOST, 0)
        await hass.services.async_call("select", "select_option",
            {"entity_id": "select.arb_zero_ee_ff_battery_protection", "option": "high"},
            blocking=True)
        mock_set.assert_awaited_with(Setting.BATTERY_PROTECTION, 2)

        assert await hass.config_entries.async_unload(entry.entry_id)
