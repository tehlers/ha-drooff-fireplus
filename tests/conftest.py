"""Fixtures for the Drooff fire+ tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.drooff_fireplus.const import CONF_FORCE_IPV4, CONF_POLLING_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

HOST = "fire"

# Panel values of a fire+ with firmware 2.4 (index: meaning)
# 2/3: Betrieb/Leistung, 4: brightness, 5: temperature, 6: air slider, 7: draught, 8: LED status,
# 9: error code, 10: ember burndown, 11: heating progress, 12: volume, 16: counter,
# 17: target temperature, 18: wood load (kg * 100), 19: door, 20: network
PANEL_V2_4 = ["0", "1", "4", "4", "60", "520", "40", "-12.4", "Gruen", "0", "0", "0", "30", "0", "0", "0", "5", "480"]
PANEL_V2_4 += ["150", "zu", "3"]
# 0: version, 1: max. temperature, 3: serial number, 4: draught available, 6: heating duration, 7: operating time
CONFIGURATION_V2_4 = ["2.4.1", "642", "0", "ABC123", "1", "0", "100", "12345"]

# Firmware 1.x: 10: LED, 11: ember burndown, 12: heating progress; Betrieb/Leistung 4/8 = burn rate 7
PANEL_V1 = ["0", "1", "4", "8", "60", "520", "40", "-12.4", "Gruen", "0", "1", "0", "50"]
CONFIGURATION_V1 = ["1.5.0", "642", "0", "DEF456", "1", "0", "0"]


# Event log (time, door, phase) of one fire from a fire+ 2.4.6: heating up, regular operation with
# door openings, ember preservation, standby. Openings within 10 minutes belong to one reload.
EVENTS = [
    (1793957890, "zu", "Anheizen"),
    (1793963280, "azu", "Anheizen"),
    (1793964530, "zu", "Regeln"),
    (1793966090, "auf", "Regeln"),
    (1793966100, "zu", "Regeln"),
    (1793968590, "auf", "Regeln"),
    (1793968600, "zu", "Regeln"),
    (1793973460, "auf", "Regeln"),
    (1793973480, "zu", "Regeln"),
    (1793973780, "azu", "Regeln"),
    (1793976380, "auf", "Regeln"),
    (1793976390, "zu", "Regeln"),
    (1793988070, "zu", "Gluehen"),
    (1793998690, "zu", "Standby"),
]


def events_response(events: list[tuple[int, str, str]]) -> str:
    """Encode events like easevents.php."""
    return '\ufeff"' + "".join(f"{time},{door},{phase}," for time, door, phase in events) + '"'


def response(values: list[str]) -> str:
    """Encode values like the fire+ web application does."""
    return '_"' + "\\n".join(values) + '"'


def mock_fireplus(
    aioclient_mock: AiohttpClientMocker,
    host: str = HOST,
    panel: list[str] | None = None,
    configuration: list[str] | None = None,
    events: list[tuple[int, str, str]] | None = None,
) -> None:
    """Answer the requests of the integration like a fire+."""
    aioclient_mock.get(f"http://{host}/php/easpanel.php", text=response(panel or PANEL_V2_4))
    aioclient_mock.get(f"http://{host}/php/easkonfig.php", text=response(configuration or CONFIGURATION_V2_4))
    aioclient_mock.post(f"http://{host}/php/easpanelW.php", text="")
    aioclient_mock.get(f"http://{host}/php/easevents.php", text=events_response(events or []))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Use a temporary configuration folder, because the integration installs its blueprints there."""
    return hass_tmp_config_dir


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for a fire+ with the default host name."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Drooff fire+",
        unique_id=f"{DOMAIN}_ABC123",
        data={CONF_HOST: HOST, CONF_FORCE_IPV4: True, CONF_POLLING_INTERVAL: 5},
    )


async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Set up the integration."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
