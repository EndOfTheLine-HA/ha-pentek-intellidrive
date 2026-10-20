"""Binary sensor platform for Pentek IntelliDrive."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PentekConfigEntry
from .entity import PentekEntity


@dataclass(frozen=True, kw_only=True)
class PentekBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a derived PID50 binary sensor."""

    value_fn: Callable[[dict[str, int | float]], bool]


BINARY_SENSOR_DESCRIPTIONS = (
    PentekBinarySensorDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: float(data.get("frequency", 0)) > 0.1,
    ),
    PentekBinarySensorDescription(
        key="sleeping",
        translation_key="sleeping",
        icon="mdi:sleep",
        value_fn=lambda data: int(data.get("operation_state", -1)) == 4,
    ),
    PentekBinarySensorDescription(
        key="fault_active",
        translation_key="fault_active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        # The fault-code register can retain a nonzero historical code while the
        # controller is healthy. States 7 and 8 are the verified active-fault
        # and fault-recovery indications.
        value_fn=lambda data: int(data.get("operation_state", -1)) in (7, 8),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up derived PID50 binary sensors."""
    async_add_entities(
        PentekBinarySensor(entry.runtime_data, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class PentekBinarySensor(PentekEntity, BinarySensorEntity):
    """A derived PID50 state."""

    entity_description: PentekBinarySensorDescription

    def __init__(self, coordinator, description: PentekBinarySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return the derived state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Require the source registers used by each derived entity."""
        if not self.coordinator.last_update_success:
            return False
        if self.entity_description.key == "running":
            return "frequency" in self.coordinator.data
        return "operation_state" in self.coordinator.data
