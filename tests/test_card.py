"""Tests for the dashboard card."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .conftest import mock_fireplus, setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
    from pytest_homeassistant_custom_component.typing import ClientSessionGenerator


async def test_card_is_served(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    """The card is served by the integration."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    client = await hass_client()
    response = await client.get("/drooff_fireplus/drooff-fireplus-card.js")
    assert response.status == 200
    assert "customElements.define" in await response.text()
