"""Diagnostics support for Pentek IntelliDrive."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import PentekConfigEntry

TO_REDACT = {"host"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PentekConfigEntry
) -> dict[str, Any]:
    """Return safe diagnostics for a PID50 entry."""
    coordinator = entry.runtime_data
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "last_slow_error": coordinator.last_slow_error,
        "register_values": coordinator.data,
    }
