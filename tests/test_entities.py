"""Tests for the entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.drooff_fireplus.const import DOMAIN

from .conftest import (
    CONFIGURATION_V1,
    CONFIGURATION_V2_4,
    PANEL_V1,
    PANEL_V2_4,
    mock_fireplus,
    response,
    setup_integration,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


def entity_id(hass: HomeAssistant, config_entry: MockConfigEntry, suffix: str) -> str:
    """Return the entity id for a unique id suffix."""
    result = er.async_get(hass).async_get_entity_id(
        suffix.split(".", maxsplit=1)[0], DOMAIN, f"{config_entry.entry_id}_{suffix.split('.')[1]}"
    )
    assert result, suffix
    return result


async def test_values(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry) -> None:
    """Values of a fire+ 2.4 are mapped to the entities."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)

    temperature = hass.states.get(entity_id(hass, config_entry, "sensor.temperature"))
    assert temperature.state == "520"
    assert temperature.attributes["max_temperature"] == 642
    assert temperature.attributes["state_class"] == "measurement"
    expected = {
        "sensor.draught": "-12.4",
        "sensor.air_slider": "40.0",
        "sensor.operation_status": "REGULAR",
        "sensor.error_message": "none",
        "sensor.target_temperature": "480",
        "sensor.weight": "1.5",
        "sensor.wifi_signal_strength": "3",
        "sensor.heating_progress": "unavailable",
        "binary_sensor.door_open": "off",
        "binary_sensor.error": "off",
        "binary_sensor.ethernet_link": "off",
        "number.burn_rate": "3",
        "number.brightness": "60",
        "number.volume": "30",
        "switch.ember_burndown": "off",
    }
    for suffix, state in expected.items():
        assert hass.states.get(entity_id(hass, config_entry, suffix)).state == state, suffix
    # firmware 2.x has no LED switch
    led = er.async_get(hass).async_get(entity_id(hass, config_entry, "switch.led"))
    assert led.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_firmware_v1(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Firmware 1.x has 7 burn rate stages and a LED switch."""
    mock_fireplus(aioclient_mock, panel=PANEL_V1, configuration=CONFIGURATION_V1)
    await setup_integration(hass, config_entry)

    burn_rate = hass.states.get(entity_id(hass, config_entry, "number.burn_rate"))
    assert burn_rate.state == "7"
    assert burn_rate.attributes["max"] == 7
    assert hass.states.get(entity_id(hass, config_entry, "switch.led")).state == "on"
    assert hass.states.get(entity_id(hass, config_entry, "switch.ember_burndown")).state == "off"


async def test_wood_urgently_required(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """The operation status shows when the fire+ urgently asks for wood."""
    panel = list(PANEL_V2_4)
    panel[8] = "Gelb blinkt"
    mock_fireplus(aioclient_mock, panel=panel)
    await setup_integration(hass, config_entry)
    state = hass.states.get(entity_id(hass, config_entry, "sensor.operation_status"))
    assert state.state == "WOOD_URGENTLY_REQUIRED"


async def test_set_burn_rate(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Setting the burn rate posts the matching Betrieb/Leistung values."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id(hass, config_entry, "number.burn_rate"), "value": 5},
        blocking=True,
    )
    posts = [call for call in aioclient_mock.mock_calls if call[0].upper() == "POST"]
    assert posts
    data = posts[-1][2]
    assert (data["Betrieb"], data["Leistung"]) == (3, 8)


async def test_write_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """A failed write raises a translated error."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    aioclient_mock.clear_requests()
    aioclient_mock.get("http://fire/php/easpanel.php", text=response(PANEL_V2_4))
    aioclient_mock.get("http://fire/php/easkonfig.php", text=response(CONFIGURATION_V2_4))
    aioclient_mock.post("http://fire/php/easpanelW.php", exc=TimeoutError())
    with pytest.raises(HomeAssistantError) as error:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": entity_id(hass, config_entry, "switch.ember_burndown")},
            blocking=True,
        )
    assert error.value.translation_key == "update_settings_failed"
