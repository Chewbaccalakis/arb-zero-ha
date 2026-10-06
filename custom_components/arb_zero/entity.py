"""Base entity for the ARB Zero integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArbZeroCoordinator


class ArbZeroEntity(CoordinatorEntity[ArbZeroCoordinator]):
    """An entity belonging to one fridge."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ArbZeroCoordinator, key: str) -> None:
        super().__init__(coordinator)
        address = coordinator.device.address
        self._attr_unique_id = f"{address}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            manufacturer="ARB",
            model="Zero Fridge Freezer",
            name=coordinator.config_entry.title,
        )
