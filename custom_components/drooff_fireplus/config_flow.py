"""Adds config flow for Drooff fire+."""

from __future__ import annotations

import socket
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    FireplusApiClient,
    FireplusApiClientCommunicationError,
    FireplusApiClientError,
)
from .const import (
    CONF_IP_VERSION,
    CONF_IP_VERSION_DEFAULT,
    CONF_POLLING_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    LOGGER,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
)


def _ip_version_to_label(ip_version: socket.AddressFamily) -> str:
    return ip_version.name.lower()


def _label_to_ip_version(label: str | None, fallback: socket.AddressFamily) -> socket.AddressFamily:
    if label and label in socket.AddressFamily:
        return socket.AddressFamily[label.upper()]
    return fallback


class FireplusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Drooff fire+."""

    VERSION = 1
    MINOR_VERSION = 1

    def _show_form(
        self, *, host: str, ip_version: str, polling_interval: str, errors: dict[str, str]
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_form(
            step_id=config_entries.SOURCE_USER,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=host,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_IP_VERSION, default=ip_version): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                _ip_version_to_label(v) for v in (socket.AF_INET, socket.AF_INET6, socket.AF_UNSPEC)
                            ],
                            translation_key=CONF_IP_VERSION,
                        )
                    ),
                    vol.Required(CONF_POLLING_INTERVAL, default=polling_interval): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_POLLING_INTERVAL,
                            max=MAX_POLLING_INTERVAL,
                            unit_of_measurement="s",
                        )
                    ),
                },
            ),
            errors=errors,
        )

    async def _get_serial_number(self, host: str, family: socket.AddressFamily) -> tuple[str | None, dict[str, str]]:
        """Connect to the fire+ endpoint and return serial number."""
        errors = {}

        client = FireplusApiClient(
            host=host,
            session=async_create_clientsession(self.hass, family=family),
        )

        try:
            response = await client.async_get_data()
        except FireplusApiClientCommunicationError as exception:
            LOGGER.error(exception)
            errors["base"] = "connection"
        except FireplusApiClientError as exception:
            LOGGER.exception(exception)
            errors["base"] = "unknown"
        else:
            return response.serial_number, errors

        return None, errors

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Verify the given user input and either create or update the config entry."""
        serial_number = None
        errors = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST, "")
            ip_version = _label_to_ip_version(user_input.get(CONF_IP_VERSION), CONF_IP_VERSION_DEFAULT)
            polling_interval = int(user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL))
            serial_number, errors = await self._get_serial_number(host, ip_version)
        elif self.source == config_entries.SOURCE_RECONFIGURE:
            existing_config_data = self._get_reconfigure_entry().data
            host = existing_config_data.get(CONF_HOST, DEFAULT_HOST)
            ip_version = socket.AddressFamily(existing_config_data.get(CONF_IP_VERSION, CONF_IP_VERSION_DEFAULT))
            polling_interval = existing_config_data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)
        else:
            host = DEFAULT_HOST
            polling_interval = DEFAULT_POLLING_INTERVAL
            ip_version: socket.AddressFamily = socket.AF_INET

        if not serial_number:
            return self._show_form(
                host=host,
                ip_version=_ip_version_to_label(ip_version),
                polling_interval=str(polling_interval),
                errors=errors,
            )

        config_data = {
            CONF_HOST: host,
            CONF_IP_VERSION: ip_version,
            CONF_POLLING_INTERVAL: polling_interval,
        }

        # In the source code of the fire+ webapp, the value we use for `serial_number` is
        # called 'hardware version'. As it looks more like a serial number, we use it as
        # such for the time being, in particular to make it part of the unique id.
        await self.async_set_unique_id(unique_id=f"{DOMAIN}_{serial_number}")

        if self.source == config_entries.SOURCE_RECONFIGURE:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=config_data,
            )

        return self.async_create_entry(
            title="Drooff fire+",
            data=config_data,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_user(user_input)
