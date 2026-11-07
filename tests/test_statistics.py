"""Tests for the statistics from the event log."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.drooff_fireplus.statistics import FireplusEvent, FireplusStatistics, parse_events

from .conftest import EVENTS, events_response, mock_fireplus, setup_integration
from .test_entities import entity_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


def test_parse_events() -> None:
    """The event log is a comma separated list of time, door and phase."""
    events = parse_events(events_response(EVENTS[:2]))
    assert events == [FireplusEvent(1793957890, "zu", "Anheizen"), FireplusEvent(1793963280, "azu", "Anheizen")]
    assert parse_events('﻿""') == []


def test_count_fire_and_reloads() -> None:
    """One fire, door openings in regular operation within 10 minutes are one reload."""
    statistics = FireplusStatistics()
    assert statistics.process(parse_events(events_response(EVENTS)), 1.5)
    assert (statistics.fires, statistics.reloads, statistics.wood) == (1, 4, 7.5)
    assert statistics.last_reload == 1793976380
    # the same events again change nothing
    assert not statistics.process(parse_events(events_response(EVENTS)), 1.5)
    assert (statistics.fires, statistics.reloads) == (1, 4)


def test_failed_heating_up_is_no_fire() -> None:
    """Heating up that ends in standby (door closed without a fire) is not counted."""
    statistics = FireplusStatistics()
    statistics.process([FireplusEvent(1, "zu", "Anheizen"), FireplusEvent(301, "zu", "Standby")], 1.5)
    assert (statistics.fires, statistics.reloads, statistics.wood) == (0, 0, 0.0)


def test_stored_statistics() -> None:
    """Statistics survive a round trip through the store, unknown keys are ignored."""
    statistics = FireplusStatistics(last_event=5, reloads=2, fires=1, wood=3.0, last_reload=4, phase="Regeln")
    assert FireplusStatistics.from_dict(statistics.as_dict() | {"unknown": 1}) == statistics
    assert FireplusStatistics.from_dict(None) == FireplusStatistics()


async def test_statistics_sensors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The sensors show the statistics, new events are read every minute and survive a reload."""
    mock_fireplus(aioclient_mock, events=EVENTS)
    await setup_integration(hass, config_entry)

    def state(key: str) -> str:
        return hass.states.get(entity_id(hass, config_entry, f"sensor.{key}")).state

    assert (state("fires"), state("reloads"), state("wood_consumption")) == ("1", "4", "7.5")
    assert state("last_reload") == "2026-11-06T14:46:20+00:00"

    later = [*EVENTS, (1794010000, "zu", "Anheizen"), (1794011000, "zu", "Regeln"), (1794013000, "auf", "Regeln")]
    aioclient_mock.clear_requests()
    mock_fireplus(aioclient_mock, events=later)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert (state("fires"), state("reloads"), state("wood_consumption")) == ("2", "5", "10.5")
    assert any("easevents.php?id=1793998690" in str(call[1]) for call in aioclient_mock.mock_calls)

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert (state("fires"), state("reloads"), state("wood_consumption")) == ("2", "5", "10.5")


async def test_without_event_log(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Without an event log (older firmware) the integration works, the statistics are unavailable."""
    # the first matching answer wins
    aioclient_mock.get("http://fire/php/easevents.php", status=404)
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "sensor.temperature")).state == "520"
    assert entity_id(hass, config_entry, "sensor.reloads")
    assert hass.states.get(entity_id(hass, config_entry, "sensor.reloads")) is None


def test_wood_without_load_is_booked_later() -> None:
    """On the first start in standby the fire+ reports no wood load: it is added once one is known."""
    statistics = FireplusStatistics()
    statistics.process(parse_events(events_response(EVENTS)), 0.0)
    assert (statistics.fires, statistics.reloads, statistics.wood, statistics.wood_pending) == (1, 4, 0.0, 5)
    assert statistics.process([], 1.5)
    assert (statistics.wood, statistics.wood_pending) == (7.5, 0)


def test_last_known_wood_load_is_used() -> None:
    """While the fire+ reports no wood load, the last known one is used."""
    statistics = FireplusStatistics()
    statistics.process([FireplusEvent(1, "zu", "Anheizen"), FireplusEvent(2, "zu", "Regeln")], 2.0)
    statistics.process([FireplusEvent(700, "auf", "Regeln")], None)
    assert (statistics.fires, statistics.reloads, statistics.wood) == (1, 1, 4.0)
