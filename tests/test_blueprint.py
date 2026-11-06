"""Tests for the wood required blueprint and its installation."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from custom_components.drooff_fireplus import BLUEPRINTS, async_install_blueprints

from .conftest import mock_fireplus, setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

BLUEPRINT = "drooff_fireplus/wood_required_notification.yaml"
STATUS = "sensor.drooff_fire_operation_status"


def installed(hass: HomeAssistant) -> Path:
    """Return the path of the installed blueprint."""
    return Path(hass.config.path("blueprints", "automation", BLUEPRINT))


async def test_blueprint_is_installed_and_updated(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Setting up the integration installs the blueprint, a changed copy is replaced and automations reloaded."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    source = BLUEPRINTS / "automation" / "wood_required_notification.yaml"
    assert installed(hass).read_bytes() == source.read_bytes()

    reloads = async_mock_service(hass, "automation", "reload")
    await async_install_blueprints(hass)
    assert reloads == []

    installed(hass).write_text("old version", encoding="utf-8")
    await async_install_blueprints(hass)
    assert installed(hass).read_bytes() == source.read_bytes()
    assert len(reloads) == 1


def notify(action: str, **data: Any) -> list[dict[str, Any]]:
    """Return a notify action as the blueprint editor creates it."""
    return [{"action": action, "data": {"title": "{{ title }}", "message": "{{ text }}", **data}}]


async def setup_automation(hass: HomeAssistant, inputs: dict[str, Any]) -> None:
    """Install the blueprint and create an automation from it."""
    await async_install_blueprints(hass)
    hass.states.async_set(STATUS, "REGULAR")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "id": "wood",
                "use_blueprint": {"path": BLUEPRINT, "input": {"status_sensor": STATUS, **inputs}},
            }
        },
    )
    await hass.async_block_till_done()


async def settle() -> None:
    """Let the automation run until it waits for a delay (async_block_till_done would wait for the delay too)."""
    for _ in range(50):
        await asyncio.sleep(0)


async def set_status(hass: HomeAssistant, status: str) -> None:
    """Change the operation status."""
    hass.states.async_set(STATUS, status)
    await settle()


async def wait(hass: HomeAssistant, minutes: int) -> None:
    """Let some minutes pass."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=minutes, seconds=1))
    await settle()


async def test_default_is_a_home_assistant_notification(hass: HomeAssistant) -> None:
    """By default a Home Assistant notification is created."""
    persistent = async_mock_service(hass, "notify", "persistent_notification")
    await setup_automation(hass, {})
    await set_status(hass, "WOOD_REQUIRED")
    assert [call.data for call in persistent] == [{"title": "Kaminofen", "message": "Bitte Holz nachlegen."}]


async def test_all_channels_can_be_empty(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Every channel is optional."""
    persistent = async_mock_service(hass, "notify", "persistent_notification")
    await setup_automation(hass, {"notify_actions": []})
    await set_status(hass, "WOOD_REQUIRED")
    await wait(hass, 1)
    assert persistent == []
    assert "Error" not in caplog.text


async def test_each_channel_after_its_delay(hass: HomeAssistant) -> None:
    """Every channel waits for its own delay."""
    pushover = async_mock_service(hass, "notify", "pushover")
    alexa = async_mock_service(hass, "notify", "alexa_media")
    lights = async_mock_service(hass, "light", "turn_on")
    await setup_automation(
        hass,
        {
            "notify_actions": notify("notify.pushover", data={"priority": 1}),
            "alexa_media_players": ["media_player.kitchen"],
            "echo_message": "Holz bitte",
            "echo_delay": {"minutes": 5},
            "custom_actions": [{"action": "light.turn_on", "data": {"entity_id": "light.hall", "flash": "short"}}],
            "custom_delay": {"minutes": 10},
        },
    )
    await set_status(hass, "WOOD_REQUIRED")
    assert len(pushover) == 1
    assert pushover[0].data == {"title": "Kaminofen", "message": "Bitte Holz nachlegen.", "data": {"priority": 1}}
    assert alexa == []

    await wait(hass, 5)
    assert len(alexa) == 1
    assert alexa[0].data == {"target": ["media_player.kitchen"], "message": "Holz bitte", "data": {"type": "announce"}}
    assert lights == []

    await wait(hass, 10)
    assert len(lights) == 1
    assert len(pushover) == 1


async def test_urgent_uses_normal_actions_until_enabled(hass: HomeAssistant) -> None:
    """Without own urgent actions, the actions for wood required are used with the urgent text."""
    pushover = async_mock_service(hass, "notify", "pushover")
    await setup_automation(
        hass, {"notify_actions": notify("notify.pushover"), "urgent_notify_actions": notify("notify.pushover")}
    )
    await set_status(hass, "WOOD_URGENTLY_REQUIRED")
    assert [call.data["message"] for call in pushover] == ["Dringend Holz nachlegen!"]


async def test_urgent_actions(hass: HomeAssistant) -> None:
    """With own urgent actions enabled, wood urgently required has its own channels."""
    pushover = async_mock_service(hass, "notify", "pushover")
    phone = async_mock_service(hass, "notify", "mobile_app_phone")
    sirens = async_mock_service(hass, "siren", "turn_on")
    lights = async_mock_service(hass, "light", "turn_on")
    await setup_automation(
        hass,
        {
            "notify_actions": notify("notify.mobile_app_phone"),
            "custom_actions": [{"action": "light.turn_on", "target": {"entity_id": "light.hall"}}],
            "urgent_enabled": True,
            "urgent_notify_actions": notify("notify.pushover", data={"priority": 2}),
            "urgent_custom_actions": [{"action": "siren.turn_on", "data": {"entity_id": "siren.hall"}}],
        },
    )
    await set_status(hass, "WOOD_REQUIRED")
    assert len(phone) == 1
    assert len(lights) == 1

    await set_status(hass, "WOOD_URGENTLY_REQUIRED")
    assert [call.data for call in pushover] == [
        {"title": "Kaminofen", "message": "Dringend Holz nachlegen!", "data": {"priority": 2}}
    ]
    assert len(sirens) == 1
    assert len(phone) == 1
    assert len(lights) == 1


@pytest.mark.parametrize("new_status", ["REGULAR", "unavailable"])
async def test_no_reminder_once_wood_was_added(hass: HomeAssistant, new_status: str) -> None:
    """A pending reminder is dropped when wood is no longer required."""
    phone = async_mock_service(hass, "notify", "mobile_app_phone")
    await setup_automation(hass, {"notify_actions": notify("notify.mobile_app_phone"), "notify_delay": {"minutes": 10}})
    await set_status(hass, "WOOD_REQUIRED")
    await set_status(hass, new_status)
    await wait(hass, 10)
    assert phone == []


async def test_notify_entities_and_wood_load(hass: HomeAssistant) -> None:
    """Notify entities get the message with the recommended wood load."""
    send_message = async_mock_service(hass, "notify", "send_message")
    hass.states.async_set("sensor.drooff_fire_wood_load", "1.5")
    await setup_automation(
        hass,
        {
            "wood_load_sensor": "sensor.drooff_fire_wood_load",
            "notify_actions": [
                {
                    "action": "notify.send_message",
                    "target": {"entity_id": "notify.phone"},
                    "data": {"message": "{{ text }}"},
                }
            ],
            "alexa_notify_entities": ["notify.kitchen_announce"],
        },
    )
    await set_status(hass, "WOOD_REQUIRED")
    assert sorted((str(call.data["entity_id"]), call.data["message"]) for call in send_message) == [
        ("['notify.kitchen_announce']", "Bitte Holz nachlegen. (1.5 kg)"),
        ("['notify.phone']", "Bitte Holz nachlegen. (1.5 kg)"),
    ]


async def test_english_and_own_texts(hass: HomeAssistant) -> None:
    """The language selects the default texts, own texts replace them."""
    pushover = async_mock_service(hass, "notify", "pushover")
    await setup_automation(
        hass,
        {
            "language": "en",
            "notify_actions": notify("notify.pushover"),
            "urgent_enabled": True,
            "urgent_notify_actions": notify("notify.pushover"),
            "urgent_title": "Stove",
            "urgent_message": "Wood, quickly!",
        },
    )
    await set_status(hass, "WOOD_REQUIRED")
    await set_status(hass, "WOOD_URGENTLY_REQUIRED")
    assert [(call.data["title"], call.data["message"]) for call in pushover] == [
        ("Fireplace", "Please add wood."),
        ("Stove", "Wood, quickly!"),
    ]
