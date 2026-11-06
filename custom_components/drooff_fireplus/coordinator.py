"""DataUpdateCoordinator for drooff_fireplus."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import FireplusApiClientError
from .const import DOMAIN, LOGGER, UPDATE_FAILED_MSG
from .statistics import FireplusStatistics, parse_events

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from .api import FireplusResponse
    from .data import FireplusConfigEntry


STATISTICS_STORAGE_VERSION = 1
# Delay before the statistics are written to disk (s)
STATISTICS_SAVE_DELAY = 30

# Like the web app: warn when the door is open longer than 5 minutes while the stove is hotter than 40 °C
DOOR_OPEN_TEMPERATURE = 40
DOOR_OPEN_TOO_LONG = timedelta(minutes=5)


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
        # Since when the door is open while the stove is hot
        self.door_open_since: datetime | None = None
        self.door_open_too_long: bool | None = None
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
                data = await self.config_entry.runtime_data.client.async_get_data()
            except FireplusApiClientError as exception:
                retries += 1
                if retries < max_retries:
                    await asyncio.sleep(1)
                else:
                    raise UpdateFailed(exception) from exception
            else:
                self._track_door(data)
                return data

        raise UpdateFailed(UPDATE_FAILED_MSG)

    def _track_door(self, data: FireplusResponse) -> None:
        """Track how long the door has been open while the stove is hot."""
        if data.door_open is None:
            too_long = None
        else:
            if data.door_open and data.temperature > DOOR_OPEN_TEMPERATURE:
                if self.door_open_since is None:
                    self.door_open_since = dt_util.utcnow()
            else:
                self.door_open_since = None
            too_long = self.door_open_since is not None and dt_util.utcnow() - self.door_open_since > DOOR_OPEN_TOO_LONG
        if too_long != self.door_open_too_long:
            self.door_open_too_long = too_long
            # identical responses of the fire+ do not update the entities, so do it here
            if self.data is not None and data == self.data:
                self.async_update_listeners()

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
