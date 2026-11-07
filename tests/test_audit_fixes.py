"""Tests for overlapping writes, Blue Angel burn rates and reloading after a reconfiguration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.drooff_fireplus import api

from .conftest import mock_fireplus, setup_integration
from .test_config_flow import USER_INPUT
from .test_controls import panel, set_number
from .test_entities import entity_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker


@pytest.fixture(autouse=True)
def no_settings_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not wait for the fire+ after a write."""
    monkeypatch.setattr(api, "SETTINGS_DELAY", 0)


def requests(aioclient_mock: AiohttpClientMocker) -> list[str]:
    """Return the requests as 'read' (panel) and 'write'."""
    names = []
    for call in aioclient_mock.mock_calls:
        url = str(call[1])
        if url.endswith("easpanelW.php"):
            names.append("write")
        elif url.endswith("easpanel.php"):
            names.append("read")
    return names


async def test_writes_do_not_overlap(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Two settings at once: the second write reads the settings again after the first one."""
    mock_fireplus(aioclient_mock)
    await setup_integration(hass, config_entry)
    aioclient_mock.mock_calls.clear()
    client = config_entry.runtime_data.client
    request = client._api_wrapper  # noqa: SLF001 make the fire+ answer slowly, like over Wifi

    async def slow_request(*args: object, **kwargs: object) -> str:
        await asyncio.sleep(0.05)
        return await request(*args, **kwargs)

    with (
        patch.object(config_entry.runtime_data.coordinator, "async_request_refresh"),
        patch.object(client, "_api_wrapper", slow_request),
    ):
        await asyncio.gather(
            set_number(hass, config_entry, "burn_rate", 5),
            hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": entity_id(hass, config_entry, "switch.ember_burndown")},
                blocking=True,
            ),
        )
    assert requests(aioclient_mock) == ["read", "write", "read", "write"]


@pytest.mark.parametrize("value", [2, 3, 4, 5])
async def test_blue_angel_refuses_intermediate_burn_rates(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry, value: int
) -> None:
    """Home Assistant does not check the step, so the integration refuses stages 2 to 5."""
    mock_fireplus(aioclient_mock, panel=panel(i13="2"))
    await setup_integration(hass, config_entry)
    aioclient_mock.mock_calls.clear()
    with pytest.raises(ServiceValidationError) as error:
        await set_number(hass, config_entry, "burn_rate", value)
    assert error.value.translation_key == "burn_rate_blue_angel"
    assert "write" not in requests(aioclient_mock)


async def test_blue_angel_accepts_power(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """Eco and Power can be set."""
    mock_fireplus(aioclient_mock, panel=panel(i13="2"))
    await setup_integration(hass, config_entry)
    aioclient_mock.mock_calls.clear()
    await set_number(hass, config_entry, "burn_rate", 6)
    assert "write" in requests(aioclient_mock)


async def test_reconfigure_reloads_once(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    """A reconfiguration reloads the entry once, not twice."""
    mock_fireplus(aioclient_mock)
    mock_fireplus(aioclient_mock, host="fire.local")
    await setup_integration(hass, config_entry)
    with patch.object(hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload) as reload:
        result = await config_entry.start_reconfigure_flow(hass)
        await hass.config_entries.flow.async_configure(result["flow_id"], {**USER_INPUT, "host": "fire.local"})
        await hass.async_block_till_done()
    assert reload.call_count == 1
