"""Sensor platform for Pentek IntelliDrive."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PentekConfigEntry
from .entity import PentekEntity
from .registers import REGISTER_BY_KEY, REGISTERS, RegisterDefinition

DEVICE_CLASSES = {
    "pressure": SensorDeviceClass.PRESSURE,
    "frequency": SensorDeviceClass.FREQUENCY,
    "power": SensorDeviceClass.POWER,
    "current": SensorDeviceClass.CURRENT,
    "voltage": SensorDeviceClass.VOLTAGE,
    "temperature": SensorDeviceClass.TEMPERATURE,
}
STATE_CLASSES = {"measurement": SensorStateClass.MEASUREMENT}


def _description(register: RegisterDefinition) -> SensorEntityDescription:
    """Build a Home Assistant description from the protocol definition."""
    return SensorEntityDescription(
        key=register.key,
        translation_key=register.key,
        native_unit_of_measurement=register.unit,
        device_class=(
            SensorDeviceClass.ENUM
            if register.enum_map is not None
            else DEVICE_CLASSES.get(register.device_class)
        ),
        state_class=STATE_CLASSES.get(register.state_class),
        icon=register.icon,
        options=(
            [*register.enum_map.values(), "unknown"]
            if register.enum_map is not None
            else None
        ),
        entity_category=(
            None if register.enabled_default else EntityCategory.DIAGNOSTIC
        ),
        entity_registry_enabled_default=register.enabled_default,
    )


SENSOR_DESCRIPTIONS = tuple(_description(register) for register in REGISTERS)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up PID50 sensors."""
    async_add_entities(
        PentekSensor(entry.runtime_data, description)
        for description in SENSOR_DESCRIPTIONS
    )


class PentekSensor(PentekEntity, SensorEntity):
    """Representation of one PID50 register."""

    entity_description: SensorEntityDescription

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._register = REGISTER_BY_KEY[description.key]

    @property
    def native_value(self) -> int | float | str | None:
        """Return the decoded register value."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        if self._register.enum_map is None:
            return value
        return self._register.enum_map.get(int(value), "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, int | float] | None:
        """Expose the numeric source value for enum sensors."""
        if self._register.enum_map is None:
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        return {"raw_value": value} if value is not None else None
