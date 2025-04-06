"""DataUpdateCoordinator for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    FireplusApiClientAuthenticationError,
    FireplusApiClientError,
)

if TYPE_CHECKING:
    from .data import FireplusConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class FireplusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: FireplusConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except FireplusApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except FireplusApiClientError as exception:
            raise UpdateFailed(exception) from exception
