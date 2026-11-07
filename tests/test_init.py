"""Tests for setup, polling and availability."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .conftest import mock_fireplus, setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


def configuration_requests(aioclient_mock: AiohttpClientMocker) -> int:
    """Count the requests of easkonfig.php."""
    return sum(1 for call in aioclient_mock.mock_calls if "easkonfig" in str(call[1]))


async def test_setup_and_unload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The entry is set up with a device and can be unloaded."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    device = dr.async_entries_for_config_entry(dr.async_get(hass), config_entry.entry_id)[0]
    assert device.manufacturer == "Drooff"
    assert device.model == "fire+"
    assert device.sw_version == "2.4.1"
    assert device.serial_number == "ABC123"

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_when_unreachable(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Setup is retried later when the fire+ cannot be reached."""
    aioclient_mock.get("http://fire/php/easpanel.php", exc=TimeoutError())
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_configuration_is_cached(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The configuration is only requested every 60 s."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    before = configuration_requests(aioclient_mock)
    for step in range(1, 4):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6 * step))
        await hass.async_block_till_done()
    assert configuration_requests(aioclient_mock) == before


async def test_all_entities_unavailable_when_offline(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Every entity becomes unavailable when the fire+ goes offline."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)

    aioclient_mock.clear_requests()
    aioclient_mock.get("http://fire/php/easpanel.php", exc=TimeoutError())
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_ids = [
        entry.entity_id
        for entry in er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
        if not entry.disabled
    ]
    assert entity_ids
    for entity_id in entity_ids:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE, entity_id
