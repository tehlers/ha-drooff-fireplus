"""
Custom integration to integrate drooff_fireplus with Home Assistant.

For more details about this integration, please refer to
https://github.com/tehlers/ha-drooff-fireplus
"""

from __future__ import annotations

import hashlib
import logging
import socket
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import CONF_HOST, Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.start import async_at_started
from homeassistant.loader import async_get_loaded_integration

from custom_components.drooff_fireplus.const import (
    CARD_FILENAME,
    CARD_URL,
    CARD_VERSION,
    CONF_FORCE_IPV4,
    CONF_FORCE_IPV4_DEFAULT,
    CONF_POLLING_INTERVAL,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
)

from .api import FireplusApiClient
from .coordinator import FireplusDataUpdateCoordinator, statistics_store
from .data import FireplusData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .data import FireplusConfigEntry

_LOGGER = logging.getLogger(__name__)

EVENTS_INTERVAL = timedelta(seconds=60)

BLUEPRINTS = Path(__file__).parent / "blueprints"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,  # noqa: ARG001 Unused function argument: `config`
) -> bool:
    """Serve the dashboard card and load it in the frontend."""
    if hass.http is not None:
        card = Path(__file__).parent / "frontend" / CARD_FILENAME
        # the hash changes with every edit of the card, so browsers never keep an old copy
        digest = await hass.async_add_executor_job(lambda: hashlib.sha256(card.read_bytes()).hexdigest()[:8])
        await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(card), cache_headers=False)])
        add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}-{digest}")

    # after start, so Home Assistant has created the blueprint folders with its own examples first
    async_at_started(hass, async_install_blueprints)
    return True


def _copy_blueprints(hass: HomeAssistant) -> set[str]:
    """Copy the blueprints of the integration to the configuration, return the domains of updated ones."""
    updated = set()
    for source in sorted(BLUEPRINTS.glob("*/*.yaml")):
        blueprint_domain = source.parent.name
        target = Path(hass.config.path("blueprints", blueprint_domain, DOMAIN, source.name))
        content = source.read_bytes()
        exists = target.is_file()
        if exists and target.read_bytes() == content:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if exists:
            updated.add(blueprint_domain)
        _LOGGER.info("Installed blueprint %s", target)
    return updated


async def async_install_blueprints(hass: HomeAssistant) -> None:
    """Install or update the blueprints of the integration."""
    try:
        updated = await hass.async_add_executor_job(_copy_blueprints, hass)
    except OSError as err:
        _LOGGER.warning("Could not install the blueprints: %s", err)
        return
    # automations keep the blueprint they were loaded with, a reload picks up the new version
    if "automation" in updated and hass.services.has_service("automation", "reload"):
        await hass.services.async_call("automation", "reload")


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: FireplusConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = FireplusDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
        update_interval=timedelta(seconds=entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)),
        host=entry.data[CONF_HOST],
    )
    entry.runtime_data = FireplusData(
        client=FireplusApiClient(
            host=entry.data[CONF_HOST],
            session=async_get_clientsession(
                hass,
                family=socket.AF_INET if entry.data.get(CONF_FORCE_IPV4, CONF_FORCE_IPV4_DEFAULT) else socket.AF_UNSPEC,
            ),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    # statistics from the event log, read less often than the values
    await coordinator.async_load_statistics()
    await coordinator.async_update_statistics()
    entry.async_on_unload(async_track_time_interval(hass, coordinator.async_update_statistics, EVENTS_INTERVAL))
    # result of the last software update, only read while one of its sensors is enabled
    entry.async_on_unload(async_track_time_interval(hass, coordinator.async_update_update_status, EVENTS_INTERVAL))

    # reconfiguration and a new IP address from DHCP reload the entry themselves
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: FireplusConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    await entry.runtime_data.coordinator.async_save_statistics()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: FireplusConfigEntry,
) -> None:
    """Delete the stored statistics of a removed entry."""
    await statistics_store(hass, entry.entry_id).async_remove()
