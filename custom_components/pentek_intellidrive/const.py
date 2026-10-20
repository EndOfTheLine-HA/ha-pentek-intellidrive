"""Constants for the Pentek IntelliDrive integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "pentek_intellidrive"

CONF_UNIT_ID: Final = "unit_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_NAME: Final = "Pentek IntelliDrive PID50"
DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 2
DEFAULT_TIMEOUT: Final = 10
DEFAULT_SCAN_INTERVAL: Final = 15
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 300
MESSAGE_WAIT_SECONDS: Final = 0.1
SLOW_REFRESH_SECONDS: Final = 1800

MANUFACTURER: Final = "Pentek"
MODEL: Final = "IntelliDrive PID50"

PLATFORMS: Final = ["sensor", "binary_sensor"]
