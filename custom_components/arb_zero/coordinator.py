"""Polling coordinator for the ARB Zero integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .device import ArbZeroDevice, ArbZeroError
from .protocol import ArbZeroStatus, Setting

_LOGGER = logging.getLogger(__name__)

type ArbZeroConfigEntry = ConfigEntry[ArbZeroCoordinator]


class ArbZeroCoordinator(DataUpdateCoordinator[ArbZeroStatus]):
    """Polls the fridge and sends setting changes."""

    config_entry: ArbZeroConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ArbZeroConfigEntry, device: ArbZeroDevice
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.device = device

    async def _async_update_data(self) -> ArbZeroStatus:
        try:
            return await self.device.async_get_status()
        except ArbZeroError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set(self, setting: Setting, value: int) -> None:
        """Send a setting change, then refresh the state."""
        try:
            await self.device.async_set(setting, value)
        except ArbZeroError as err:
            raise HomeAssistantError(str(err)) from err
        await self.async_request_refresh()
