"""Base entity for Pentek IntelliDrive."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import PentekCoordinator


class PentekEntity(CoordinatorEntity[PentekCoordinator]):
    """Base for entities backed by the PID50 coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PentekCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        identifier = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{identifier}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
            configuration_url=f"http://{entry.data['host']}",
        )

    @property
    def available(self) -> bool:
        """Return whether this entity has current data."""
        return (
            super().available and self.entity_description.key in self.coordinator.data
        )
