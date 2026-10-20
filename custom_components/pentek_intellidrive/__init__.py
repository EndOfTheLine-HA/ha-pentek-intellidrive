"""Pentek IntelliDrive integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .api import PentekModbusClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    MESSAGE_WAIT_SECONDS,
    PLATFORMS,
)
from .coordinator import PentekCoordinator

type PentekConfigEntry = ConfigEntry[PentekCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PentekConfigEntry) -> bool:
    """Set up Pentek IntelliDrive from a config entry."""
    scan_interval = int(
        entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
    )
    client = PentekModbusClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        unit_id=entry.data[CONF_UNIT_ID],
        timeout=DEFAULT_TIMEOUT,
        message_wait=MESSAGE_WAIT_SECONDS,
    )
    coordinator = PentekCoordinator(hass, entry, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PentekConfigEntry) -> bool:
    """Unload a Pentek IntelliDrive config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: PentekConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
