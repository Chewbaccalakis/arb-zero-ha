"""The ARB Zero fridge integration."""

from __future__ import annotations

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import ArbZeroConfigEntry, ArbZeroCoordinator
from .device import ArbZeroDevice

PLATFORMS = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ArbZeroConfigEntry) -> bool:
    """Set up an ARB Zero from a config entry."""
    device = ArbZeroDevice(hass, entry.data[CONF_ADDRESS])
    coordinator = ArbZeroCoordinator(hass, entry, device)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await device.async_disconnect()
        raise
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ArbZeroConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.device.async_disconnect()
    return unloaded
