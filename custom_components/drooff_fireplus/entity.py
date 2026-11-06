"""FireplusEntity class."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FireplusApiClientError
from .const import DOMAIN
from .coordinator import FireplusDataUpdateCoordinator


class FireplusEntity(CoordinatorEntity[FireplusDataUpdateCoordinator]):
    """FireplusEntity class."""

    def __init__(self, coordinator: FireplusDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            configuration_url=f"http://{coordinator.host}",
        )

    async def _async_update_settings(self, **settings: Any) -> None:
        """Write settings to the fire+ and read them back."""
        try:
            await self.coordinator.config_entry.runtime_data.client.async_update_settings(**settings)
        except FireplusApiClientError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="update_settings_failed",
                translation_placeholders={"error": str(exception)},
            ) from exception
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
