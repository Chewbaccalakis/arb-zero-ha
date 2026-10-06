"""Setpoint for the ARB Zero integration."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ArbZeroConfigEntry
from .entity import ArbZeroEntity
from .protocol import Setting

# ARB's published range for the Zero is -22 to +10 °C.
RANGE_C = (-22, 10)
RANGE_F = (-8, 50)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArbZeroConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the setpoint."""
    async_add_entities([ArbZeroSetpoint(entry.runtime_data, "setpoint")])


class ArbZeroSetpoint(ArbZeroEntity, NumberEntity):
    """Target temperature."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    @property
    def native_unit_of_measurement(self) -> str:
        if self.coordinator.data.fahrenheit:
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    @property
    def native_min_value(self) -> float:
        return (RANGE_F if self.coordinator.data.fahrenheit else RANGE_C)[0]

    @property
    def native_max_value(self) -> float:
        return (RANGE_F if self.coordinator.data.fahrenheit else RANGE_C)[1]

    @property
    def native_value(self) -> int:
        return self.coordinator.data.setpoint

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set(Setting.SETPOINT, round(value))
