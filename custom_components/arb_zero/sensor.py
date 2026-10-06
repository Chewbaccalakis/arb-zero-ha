"""Sensors for the ARB Zero integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ArbZeroConfigEntry
from .entity import ArbZeroEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArbZeroConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            ArbZeroTemperature(coordinator, "temperature"),
            ArbZeroRawByte(coordinator, "raw_byte_11"),
        ]
    )


class ArbZeroTemperature(ArbZeroEntity, SensorEntity):
    """Cabinet temperature."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        if self.coordinator.data.fahrenheit:
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> int:
        return self.coordinator.data.temperature


class ArbZeroRawByte(ArbZeroEntity, SensorEntity):
    """Undecoded value, possibly supply voltage."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int:
        return self.coordinator.data.raw_byte_11
