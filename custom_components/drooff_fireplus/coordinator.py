"""DataUpdateCoordinator for drooff_fireplus."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FireplusApiClientError
from .const import DOMAIN, LOGGER, UPDATE_FAILED_MSG
from .statistics import FireplusStatistics, parse_events

if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from homeassistant.core import HomeAssistant

    from .data import FireplusConfigEntry


STATISTICS_STORAGE_VERSION = 1
# Delay before the statistics are written to disk (s)
STATISTICS_SAVE_DELAY = 30


def statistics_store(hass: HomeAssistant, entry_id: str) -> Store[dict]:
    """Return the store of the statistics of a config entry."""
    return Store(hass, STATISTICS_STORAGE_VERSION, f"{DOMAIN}.{entry_id}.statistics")


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class FireplusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Drooff fire+ API."""

    config_entry: FireplusConfigEntry
    host: str

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: FireplusConfigEntry,
        update_interval: timedelta,
        host: str,
    ) -> None:
        """Initialize the FireplusDataUpdateCoordinator."""
        self.host = host
        self.statistics = FireplusStatistics()
        # None until the event log was read once, False if the fire+ has none
        self.events_supported: bool | None = None
        self._statistics_store: Store[dict] = statistics_store(hass, config_entry.entry_id)
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=update_interval,
            # entities are only written when the fire+ reports something new
            always_update=False,
        )

    async def _async_update_data(self) -> Any:
        """Retrieve updated data from Drooff fire+ API."""
        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                return await self.config_entry.runtime_data.client.async_get_data()
            except FireplusApiClientError as exception:
                retries += 1
                if retries < max_retries:
                    await asyncio.sleep(1)
                else:
                    raise UpdateFailed(exception) from exception

        raise UpdateFailed(UPDATE_FAILED_MSG)

    async def async_load_statistics(self) -> None:
        """Restore the statistics of the last run."""
        self.statistics = FireplusStatistics.from_dict(await self._statistics_store.async_load())

    async def async_save_statistics(self) -> None:
        """Write the statistics now, for example before the entry is unloaded."""
        await self._statistics_store.async_save(self.statistics.as_dict())

    async def async_update_statistics(self, _now: datetime | None = None) -> None:
        """Read new entries of the event log and update the statistics."""
        try:
            response = await self.config_entry.runtime_data.client.async_get_events(self.statistics.last_event)
        except FireplusApiClientError as exception:
            # older firmware has no event log; the statistics are not important enough for an error
            if self.events_supported is None:
                self.events_supported = False
                self.async_update_listeners()
            LOGGER.debug("Reading the event log failed: %s", exception)
            return
        first = self.events_supported is not True
        self.events_supported = True
        weight = self.data.weight if self.data is not None else None
        if self.statistics.process(parse_events(response), weight):
            self._statistics_store.async_delay_save(self.statistics.as_dict, STATISTICS_SAVE_DELAY)
            self.async_update_listeners()
        elif first:
            self.async_update_listeners()
