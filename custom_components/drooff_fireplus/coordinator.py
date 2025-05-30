"""DataUpdateCoordinator for drooff_fireplus."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FireplusApiClientError
from .const import DOMAIN, LOGGER, UPDATE_FAILED_MSG

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.core import HomeAssistant

    from .data import FireplusConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class FireplusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Drooff fire+ API."""

    config_entry: FireplusConfigEntry
    host: str

    def __init__(self, hass: HomeAssistant, update_interval: timedelta, host: str) -> None:
        """Initialize the FireplusDataUpdateCoordinator."""
        self.host = host
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
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
