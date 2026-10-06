"""Selects for the ARB Zero integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ArbZeroConfigEntry
from .entity import ArbZeroEntity
from .protocol import BATTERY_LEVELS, Setting

UNITS = ("celsius", "fahrenheit")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArbZeroConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up selects."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            ArbZeroBatteryProtection(coordinator, "battery_protection"),
            ArbZeroDisplayUnit(coordinator, "display_unit"),
        ]
    )


class ArbZeroBatteryProtection(ArbZeroEntity, SelectEntity):
    """Low-voltage cut-out level."""

    _attr_options = list(BATTERY_LEVELS)
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.battery_protection

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set(
            Setting.BATTERY_PROTECTION, BATTERY_LEVELS.index(option)
        )


class ArbZeroDisplayUnit(ArbZeroEntity, SelectEntity):
    """Unit shown on the fridge's display."""

    _attr_options = list(UNITS)
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def current_option(self) -> str:
        return UNITS[self.coordinator.data.fahrenheit]

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set(Setting.DISPLAY_UNIT, UNITS.index(option))
