"""Exercise the connection class with a fake Bleak client."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.arb_zero.device import ArbZeroDevice, ArbZeroError
from custom_components.arb_zero.protocol import NOTIFY_UUID, WRITE_UUID, Setting

REPLY = bytes.fromhex("aac1f2a00305f9f800000a0d0000000e")


class FakeClient:
    def __init__(self, reply=True):
        self.is_connected = True
        self.writes = []
        self._cb = None
        self._reply = reply

    async def start_notify(self, uuid, cb):
        assert uuid == NOTIFY_UUID
        self._cb = cb

    async def write_gatt_char(self, uuid, data, response):
        assert uuid == WRITE_UUID
        self.writes.append(bytes(data))
        if self._reply and data[2] == 0xF0:
            self._cb(None, bytearray(REPLY))

    async def disconnect(self):
        self.is_connected = False


async def _device(hass, client):
    dev = ArbZeroDevice(hass, "AA:BB:CC:DD:EE:FF")
    connect = patch(
        "custom_components.arb_zero.device.establish_connection",
        return_value=client,
    )
    found = patch(
        "custom_components.arb_zero.device.bluetooth.async_ble_device_from_address",
        return_value=MagicMock(),
    )
    return dev, connect, found


async def test_status_and_command(hass):
    client = FakeClient()
    dev, connect, found = await _device(hass, client)
    with connect as mock_connect, found:
        status = await dev.async_get_status()
        assert status.temperature == -7
        await dev.async_set(Setting.SETPOINT, -6)
        await dev.async_get_status()
    assert mock_connect.call_count == 1  # connection is reused
    assert client.writes[1].hex() == "aac1f100000000fa0001000000000058"


async def test_timeout_disconnects(hass):
    client = FakeClient(reply=False)
    dev, connect, found = await _device(hass, client)
    with connect, found, patch("custom_components.arb_zero.device.REPLY_TIMEOUT", 0.05):
        with pytest.raises(ArbZeroError):
            await dev.async_get_status()
    assert not client.is_connected


async def test_not_found(hass):
    dev = ArbZeroDevice(hass, "AA:BB:CC:DD:EE:FF")
    with patch(
        "custom_components.arb_zero.device.bluetooth.async_ble_device_from_address",
        return_value=None,
    ), pytest.raises(ArbZeroError):
        await dev.async_get_status()
