"""Tests for the software update information of the fire+."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import PropertyMock, patch

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.drooff_fireplus.api import FireplusUpdateResult, FireplusUpdateStatus

from .conftest import UPDATE, mock_fireplus, setup_integration
from .test_entities import entity_id

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Enable all entities, also those that are disabled by default."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
        new_callable=PropertyMock,
    ):
        yield


async def test_update_sensors_disabled_by_default(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The sensors have to be enabled, until then the update pages are not read."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    for suffix in ("sensor.update_result", "sensor.update_schedule"):
        entry = er.async_get(hass).async_get(entity_id(hass, config_entry, suffix))
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert not any("Update" in str(call[1]) for call in aioclient_mock.mock_calls)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_update_sensors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The answers recorded from a fire+ 2.4.6 are shown."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    result = hass.states.get(entity_id(hass, config_entry, "sensor.update_result"))
    assert result.state == "no_updates"
    assert result.attributes["code"] == 2
    assert (
        result.attributes["message"]
        == "Es sind keine neuen Updates verfügbar, das System ist auf dem aktuellsten Stand"
    )
    schedule = hass.states.get(entity_id(hass, config_entry, "sensor.update_schedule"))
    assert schedule.state == "Mittwoch, 03:43 Uhr"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_without_update_information(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Older firmware without these pages leaves the sensors unavailable."""
    # the first matching mock answers
    aioclient_mock.get("http://fire/php/UpdateErgebniss.php", status=404)
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "sensor.update_result")).state == "unavailable"
    assert config_entry.runtime_data.coordinator.update_supported is False


@pytest.mark.parametrize(
    ("answer", "result"),
    [
        ('﻿"0, Update nicht gestartet\\n"', FireplusUpdateResult.NOT_STARTED),
        ('﻿"3, Update l\\u00e4uft\\n"', FireplusUpdateResult.RUNNING),
        ('﻿"6, Ofen in Betrieb\\n"', FireplusUpdateResult.POSTPONED),
        ('﻿"9, ?\\n"', FireplusUpdateResult.UNKNOWN),
        ('﻿""', FireplusUpdateResult.UNKNOWN),
    ],
)
def test_parse(answer: str, result: FireplusUpdateResult) -> None:
    """All codes of the service page of the web app are known, others are unknown."""
    assert FireplusUpdateStatus.parse(answer, UPDATE[1]).result == result
