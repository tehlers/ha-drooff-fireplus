"""Tests for the config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.drooff_fireplus.const import CONF_FORCE_IPV4, CONF_POLLING_INTERVAL, DOMAIN

from .conftest import HOST, mock_fireplus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

USER_INPUT = {CONF_HOST: HOST, CONF_FORCE_IPV4: True, CONF_POLLING_INTERVAL: 10}
DHCP = DhcpServiceInfo(ip="192.168.1.50", hostname="fire", macaddress="aabbccddeeff")


async def test_user_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """The user enters the host name and the entry is created."""
    mock_fireplus(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == f"{DOMAIN}_ABC123"


async def test_user_flow_connection_error(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """An unreachable fire+ shows an error and the form again."""
    aioclient_mock.get(f"http://{HOST}/php/easpanel.php", exc=TimeoutError())
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


async def test_user_flow_already_configured(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The same fire+ cannot be added twice."""
    config_entry.add_to_hass(hass)
    mock_fireplus(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The host can be changed."""
    config_entry.add_to_hass(hass)
    mock_fireplus(aioclient_mock, host="fire.local")
    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**USER_INPUT, CONF_HOST: "fire.local"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_HOST] == "fire.local"


async def test_dhcp_discovery(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """A fire+ found by DHCP is set up after confirmation."""
    mock_fireplus(aioclient_mock, host=DHCP.ip)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == DHCP.ip


async def test_dhcp_updates_ip_address(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """An entry set up with an IP address follows a new IP address."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=f"{DOMAIN}_ABC123", data={**USER_INPUT, CONF_HOST: "192.168.1.9"})
    entry.add_to_hass(hass)
    mock_fireplus(aioclient_mock, host=DHCP.ip)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == DHCP.ip


async def test_dhcp_keeps_host_name(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """An entry set up with a host name keeps it."""
    config_entry.add_to_hass(hass)
    mock_fireplus(aioclient_mock, host=DHCP.ip)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP
    )
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == HOST


async def test_dhcp_unreachable(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Discovery is aborted when the fire+ does not answer."""
    aioclient_mock.get(f"http://{DHCP.ip}/php/easpanel.php", exc=TimeoutError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
