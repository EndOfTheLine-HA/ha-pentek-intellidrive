"""Config flow for Pentek IntelliDrive."""

from __future__ import annotations

import logging
from typing import Any, override

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .api import PentekConnectionError, PentekModbusClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MESSAGE_WAIT_SECONDS,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=values.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_PORT, default=values.get(CONF_PORT, DEFAULT_PORT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(
                CONF_UNIT_ID, default=values.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
            ),
        }
    )


async def _validate_input(hass, data: dict[str, Any]) -> None:
    client = PentekModbusClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        unit_id=data[CONF_UNIT_ID],
        timeout=DEFAULT_TIMEOUT,
        message_wait=MESSAGE_WAIT_SECONDS,
    )
    try:
        await hass.async_add_executor_job(client.test_connection)
    except PentekConnectionError as err:
        raise CannotConnect from err


class PentekIntelliDriveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pentek IntelliDrive."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(user_input)
            data[CONF_HOST] = data[CONF_HOST].strip()
            unique_id = (
                f"{data[CONF_HOST].lower()}:{data[CONF_PORT]}:{data[CONF_UNIT_ID]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            try:
                await _validate_input(self.hass, data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating the PID50 gateway")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Pentek PID50 ({data[CONF_HOST]})", data=data
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PentekOptionsFlow()


class PentekOptionsFlow(OptionsFlow):
    """Handle polling options."""

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    )
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate the gateway cannot be reached or validated."""
