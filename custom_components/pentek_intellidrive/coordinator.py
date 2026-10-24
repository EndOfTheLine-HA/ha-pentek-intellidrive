"""Data coordinator for Pentek IntelliDrive."""

from __future__ import annotations

import logging
from datetime import timedelta
from time import monotonic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PentekConnectionError, PentekModbusClient
from .const import DOMAIN, SLOW_REFRESH_SECONDS
from .registers import FAST_BLOCKS, SLOW_BLOCKS, merge_registers

_LOGGER = logging.getLogger(__name__)


class PentekCoordinator(DataUpdateCoordinator[dict[str, int | float]]):
    """Coordinate serialized reads from one PID50 gateway."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: PentekModbusClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            always_update=False,
        )
        self.client = client
        self._last_slow_update = 0.0
        self.last_slow_error: str | None = None

    async def _async_update_data(self) -> dict[str, int | float]:
        try:
            fast_words = await self.hass.async_add_executor_job(
                self.client.read_blocks, FAST_BLOCKS
            )
        except PentekConnectionError as err:
            raise UpdateFailed(f"PID50 communication failed: {err}") from err

        data = merge_registers(self.data or {}, fast_words)

        now = monotonic()
        if (
            not self._last_slow_update
            or now - self._last_slow_update >= SLOW_REFRESH_SECONDS
        ):
            # Record the attempt before doing I/O so a failing static block is not
            # retried on every fast update and allowed to overload the gateway.
            self._last_slow_update = now
            try:
                slow_words = await self.hass.async_add_executor_job(
                    self.client.read_blocks, SLOW_BLOCKS
                )
            except PentekConnectionError as err:
                self.last_slow_error = str(err)
                _LOGGER.warning("Unable to refresh static PID50 registers: %s", err)
            else:
                data = merge_registers(data, slow_words)
                self.last_slow_error = None

        return data
