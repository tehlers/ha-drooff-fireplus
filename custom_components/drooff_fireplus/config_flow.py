"""Adds config flow for Drooff fire+."""

from __future__ import annotations

import ipaddress
import socket
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, UnitOfTime
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .api import (
    FireplusApiClient,
    FireplusApiClientCommunicationError,
    FireplusApiClientError,
)
from .const import (
    CONF_FORCE_IPV4,
    CONF_FORCE_IPV4_DEFAULT,
    CONF_POLLING_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    LOGGER,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
)


class FireplusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Drooff fire+."""

    VERSION = 1
    MINOR_VERSION = 1

    _discovered_host: str

    def _show_form(
        self, *, host: str, force_ipv4: bool, polling_interval: int, errors: dict[str, str]
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
                    vol.Required(CONF_FORCE_IPV4, default=force_ipv4): selector.BooleanSelector(),
                    vol.Required(CONF_POLLING_INTERVAL, default=polling_interval): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_POLLING_INTERVAL,
                            max=MAX_POLLING_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                },
            ),
            errors=errors,
        )

    async def _get_serial_number(self, *, host: str, force_ipv4: bool) -> tuple[str | None, dict[str, str]]:
        """Connect to the fire+ endpoint and return serial number."""
        errors = {}

        client = FireplusApiClient(
            host=host,
            session=async_get_clientsession(self.hass, family=socket.AF_INET if force_ipv4 else socket.AF_UNSPEC),
        )

        try:
            response = await client.async_get_data()
        except FireplusApiClientCommunicationError as exception:
            # also a normal case for DHCP: another device may be called "fire"
            LOGGER.debug("Cannot connect to %s: %s", host, exception)
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
            force_ipv4 = user_input.get(CONF_FORCE_IPV4, CONF_FORCE_IPV4_DEFAULT)
            polling_interval = user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)
            serial_number, errors = await self._get_serial_number(host=host, force_ipv4=force_ipv4)
        elif self.source == config_entries.SOURCE_RECONFIGURE:
            existing_config_data = self._get_reconfigure_entry().data
            host = existing_config_data.get(CONF_HOST, DEFAULT_HOST)
            force_ipv4 = existing_config_data.get(CONF_FORCE_IPV4, CONF_FORCE_IPV4_DEFAULT)
            polling_interval = existing_config_data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)
        else:
            host = DEFAULT_HOST
            polling_interval = DEFAULT_POLLING_INTERVAL
            force_ipv4 = CONF_FORCE_IPV4_DEFAULT

        # If the serial number is not set, the form must be displayed to either capture
        # the data or to display an error message.
        if not serial_number:
            return self._show_form(
                host=host,
                force_ipv4=force_ipv4,
                polling_interval=polling_interval,
                errors=errors,
            )

        config_data = {
            CONF_HOST: host,
            CONF_FORCE_IPV4: force_ipv4,
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

        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="Drooff fire+",
            data=config_data,
        )

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> config_entries.ConfigFlowResult:
        """Handle a fire+ found by DHCP (its default hostname is 'fire')."""
        host = discovery_info.ip
        serial_number, errors = await self._get_serial_number(host=host, force_ipv4=CONF_FORCE_IPV4_DEFAULT)
        if errors or not serial_number:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(unique_id=f"{DOMAIN}_{serial_number}")
        # Follow a changed IP address, but keep host names the user entered
        for entry in self._async_current_entries(include_ignore=False):
            if entry.unique_id == self.unique_id and _is_ip_address(entry.data.get(CONF_HOST, "")):
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        self._abort_if_unique_id_configured()

        self._discovered_host = host
        self.context["title_placeholders"] = {"host": host}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Confirm the setup of a discovered fire+."""
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(
                step_id="discovery_confirm",
                description_placeholders={"host": self._discovered_host},
            )
        return self.async_create_entry(
            title="Drooff fire+",
            data={
                CONF_HOST: self._discovered_host,
                CONF_FORCE_IPV4: CONF_FORCE_IPV4_DEFAULT,
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_user(user_input)


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True
