"""Tests for the diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry

from .conftest import mock_fireplus, setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
    from pytest_homeassistant_custom_component.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    """Diagnostics contain the values without host and serial number."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    assert diagnostics["entry"]["data"]["host"] == "**REDACTED**"
    assert diagnostics["entry"]["unique_id"] == "**REDACTED**"
    assert diagnostics["data"]["serial_number"] == "**REDACTED**"
    assert diagnostics["data"]["temperature"] == 520
    assert diagnostics["data"]["operation_status"] == "REGULAR"
    assert len(diagnostics["raw_responses"]) == 2
    assert "ABC123" not in str(diagnostics)
    assert diagnostics["update_status"] is None  # its sensors are disabled by default
