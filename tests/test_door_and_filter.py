"""Tests for the door warning and the filter status of stoves with the Blue Angel label."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from .conftest import mock_fireplus, setup_integration
from .test_controls import panel
from .test_entities import entity_id

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

# Panel value 13 with bit 2: stove with the Blue Angel label
BLUE_ANGEL = {"i13": "2"}


def filter_response(code: str) -> str:
    """Encode the answer of oeko.php, as recorded from a fire+ 2.4.6."""
    return '﻿"' + code + '\\n"'


async def refresh(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    values: list[str],
) -> None:
    """Let the fire+ answer with other panel values and update the entities."""
    aioclient_mock.clear_requests()
    mock_fireplus(aioclient_mock, panel=values)
    await config_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


async def test_door_open_too_long(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Like the web app, a door open for more than 5 minutes above 40 °C is a problem."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    warning = entity_id(hass, config_entry, "binary_sensor.door_open_too_long")
    assert hass.states.get(warning).state == "off"

    open_door = panel(i19="auf")
    await refresh(hass, aioclient_mock, config_entry, open_door)
    freezer.tick(timedelta(minutes=5))
    # the same answer again: the entity is updated although the fire+ reports nothing new
    await refresh(hass, aioclient_mock, config_entry, open_door)
    assert hass.states.get(warning).state == "off"
    freezer.tick(timedelta(seconds=10))
    await refresh(hass, aioclient_mock, config_entry, open_door)
    assert hass.states.get(warning).state == "on"

    await refresh(hass, aioclient_mock, config_entry, panel(i19="zu"))
    assert hass.states.get(warning).state == "off"


async def test_door_open_on_cold_stove(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """An open door at 40 °C or less is no problem."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    cold = panel(i5="40", i19="auf")
    await refresh(hass, aioclient_mock, config_entry, cold)
    freezer.tick(timedelta(minutes=10))
    await refresh(hass, aioclient_mock, config_entry, cold)
    assert hass.states.get(entity_id(hass, config_entry, "binary_sensor.door_open_too_long")).state == "off"


@pytest.mark.parametrize(
    "case",
    [
        ("0", "driver_error", "on"),
        ("1", "not_found", "on"),
        ("2", "present", "off"),
        ("3", "inactive", "off"),
        ("4", "active", "off"),
        ("5", "cleaning_required", "on"),
        ("7", "error", "on"),
    ],
)
async def test_filter_status(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    case: tuple[str, str, str],
) -> None:
    """The answers of oeko.php are shown like in the web app."""
    code, state, problem = case
    mock_fireplus(aioclient_mock, panel=panel(**BLUE_ANGEL))
    aioclient_mock.get("http://fire/php/oeko.php", text=filter_response(code))
    await setup_integration(hass, config_entry)
    sensor = hass.states.get(entity_id(hass, config_entry, "sensor.filter_status"))
    assert sensor.state == state
    assert sensor.attributes["filter_code"] == int(code)
    assert hass.states.get(entity_id(hass, config_entry, "binary_sensor.filter_problem")).state == problem


async def test_no_filter_without_blue_angel(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Other stoves answer oeko.php too ("not found"), so it is neither read nor shown."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    assert not any("oeko.php" in str(call[1]) for call in aioclient_mock.mock_calls)
    assert hass.states.get(entity_id(hass, config_entry, "sensor.filter_status")) is None


async def test_filter_failure_keeps_other_values(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """If oeko.php fails, only the filter status is unavailable."""
    mock_fireplus(aioclient_mock, panel=panel(**BLUE_ANGEL))
    aioclient_mock.get("http://fire/php/oeko.php", status=500)
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "sensor.filter_status")).state == "unavailable"
    assert hass.states.get(entity_id(hass, config_entry, "sensor.temperature")).state == "520"
