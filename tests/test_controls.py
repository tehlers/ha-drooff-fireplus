"""Tests for the control mode, locked settings and the newer configuration values."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .conftest import PANEL_V2_4, mock_fireplus, setup_integration
from .test_entities import entity_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

# Web app 2.1.8 on firmware 2.4.6 sends 11 configuration values:
# 2: automatic updates, 5: online support, 8: web app version, 9: not a Pi Zero, 10: draught warning
CONFIGURATION_V2_4_6 = ["2.4.6", "650", "1", "ABC123", "1", "0", "900", "40810", "2.1.8", "1", "1"]


def panel(**changes: str) -> list[str]:
    """Return the panel values of a fire+ 2.4 with some values changed (key: index)."""
    values = list(PANEL_V2_4)
    for index, value in changes.items():
        values[int(index.removeprefix("i"))] = value
    return values


def posts(aioclient_mock: AiohttpClientMocker) -> list:
    """Return the write requests."""
    return [call for call in aioclient_mock.mock_calls if call[0].upper() == "POST"]


async def set_number(hass: HomeAssistant, config_entry: MockConfigEntry, key: str, value: float) -> None:
    """Set a number entity."""
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id(hass, config_entry, f"number.{key}"), "value": value},
        blocking=True,
    )


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_configuration_of_newer_web_app(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Online support, automatic updates, draught warning and the web app version are shown."""
    mock_fireplus(aioclient_mock, configuration=CONFIGURATION_V2_4_6)
    await setup_integration(hass, config_entry)
    expected = {
        "binary_sensor.online_support": "off",
        "binary_sensor.auto_update": "on",
        "binary_sensor.draught_warning": "on",
        "sensor.web_app_version": "2.1.8",
        "sensor.control_mode": "web",
    }
    for suffix, state in expected.items():
        assert hass.states.get(entity_id(hass, config_entry, suffix)).state == state, suffix


async def test_older_configuration_has_no_extras(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """With 8 configuration values the newer entities are unavailable."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "binary_sensor.online_support")) is None


@pytest.mark.parametrize(
    "case",
    [
        ({"i14": "1", "i15": "0"}, "remote_control", ["burn_rate", "brightness", "volume"], []),
        ({"i14": "1", "i15": "1"}, "remote_control_automatic", ["burn_rate", "brightness"], []),
        ({"i15": "3"}, "room_controller", ["burn_rate"], ["brightness"]),
        ({"i0": "1", "i1": "0"}, "panel", ["burn_rate"], ["volume"]),
        ({"i0": "1", "i1": "1"}, "web", [], ["burn_rate"]),
    ],
)
async def test_locked_settings(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    case: tuple[dict[str, str], str, list[str], list[str]],
) -> None:
    """Settings the web app locks are refused with a clear error, the others are written."""
    changes, mode, locked, allowed = case
    mock_fireplus(aioclient_mock, panel=panel(**changes))
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "sensor.control_mode")).state == mode

    for key in locked:
        with pytest.raises(ServiceValidationError) as error:
            await set_number(hass, config_entry, key, 1 if key == "burn_rate" else 50)
        assert error.value.translation_key == "control_locked"
    assert posts(aioclient_mock) == []

    for key in allowed:
        await set_number(hass, config_entry, key, 1 if key == "burn_rate" else 50)
    assert len(posts(aioclient_mock)) == len(allowed)


async def test_locked_switch(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The ember mode can not be changed while the remote control is used."""
    mock_fireplus(aioclient_mock, panel=panel(i14="1", i15="0"))
    await setup_integration(hass, config_entry)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id(hass, config_entry, "switch.ember_burndown")}, blocking=True
        )
    assert posts(aioclient_mock) == []


async def test_blue_angel_stove_has_two_burn_rates(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Stoves with the Blue Angel label only offer ECO (1) and POWER (6)."""
    mock_fireplus(aioclient_mock, panel=panel(i13="2"))
    await setup_integration(hass, config_entry)
    state = hass.states.get(entity_id(hass, config_entry, "number.burn_rate"))
    assert (state.attributes["min"], state.attributes["max"], state.attributes["step"]) == (1, 6, 5)


@pytest.mark.parametrize(("leistung", "burn_rate"), [("4", "1"), ("8", "4")])
async def test_betrieb_1_is_the_lowest_stage(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    leistung: str,
    burn_rate: str,
) -> None:
    """Like the web app, Betrieb 1 counts as the lowest stage of its Leistung."""
    mock_fireplus(aioclient_mock, panel=panel(i2="1", i3=leistung))
    await setup_integration(hass, config_entry)
    assert hass.states.get(entity_id(hass, config_entry, "number.burn_rate")).state == burn_rate


async def test_rarely_needed_entities_disabled(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Network, operating time and device settings have to be enabled, errors and control are shown."""
    mock_fireplus(aioclient_mock, configuration=CONFIGURATION_V2_4_6)
    await setup_integration(hass, config_entry)
    registry = er.async_get(hass)
    disabled = [
        "sensor.operating_time",
        "sensor.wifi_signal_strength",
        "sensor.web_app_version",
        "binary_sensor.ethernet_link",
        "binary_sensor.online_support",
        "binary_sensor.auto_update",
    ]
    for suffix in disabled:
        assert registry.async_get(entity_id(hass, config_entry, suffix)).disabled_by is not None, suffix
    enabled = ("binary_sensor.error", "sensor.error_message", "sensor.control_mode", "binary_sensor.draught_warning")
    for suffix in enabled:
        assert registry.async_get(entity_id(hass, config_entry, suffix)).disabled_by is None, suffix
