"""Boost switch for the ARB Zero integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ArbZeroConfigEntry
from .entity import ArbZeroEntity
from .protocol import Setting


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArbZeroConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the boost switch."""
    async_add_entities([ArbZeroBoost(entry.runtime_data, "boost")])


class ArbZeroBoost(ArbZeroEntity, SwitchEntity):
    """Boost (fast cool-down) mode."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.boost

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set(Setting.BOOST, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set(Setting.BOOST, 0)
