"""Adds config flow for Drooff fire+."""

from __future__ import annotations

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
from .const import DOMAIN, LOGGER


class FireplusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Drooff fire+."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                response = await self._test_host(
                    host=user_input[CONF_HOST],
                )
            except FireplusApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except FireplusApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                # In the source code of the fire+ webapp, the value we use for `serial_number` is
                # called 'hardware version'. As it looks more like a serial number, we use it as
                # such for the time being, in particular to make it part of the unique id.
                await self.async_set_unique_id(unique_id=f"{DOMAIN}_{response.serial_number}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Drooff fire+",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_host(self, host: str) -> Any:
        """Validate host by calling the fire+ specific endpoints and returning the parsed result."""
        client = FireplusApiClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        return await client.async_get_data()
