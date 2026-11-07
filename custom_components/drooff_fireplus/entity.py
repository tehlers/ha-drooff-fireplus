"""FireplusEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FireplusApiClientError
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import FireplusDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class FireplusEntity(CoordinatorEntity[FireplusDataUpdateCoordinator]):
    """FireplusEntity class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: EntityDescription,
        unique_id_suffix: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{unique_id_suffix or description.key}"
        data = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=data.serial_number if data else None,
            sw_version=str(data.version) if data else None,
            configuration_url=f"http://{coordinator.host}",
        )

    async def _async_update_settings(self, **settings: Any) -> None:
        """Write settings to the fire+ and read them back."""
        data = self.coordinator.data
        if data is not None and data.control_mode is not None and data.locked_settings & settings.keys():
            # the fire+ ignores these settings while a remote control, room controller or the panel controls it
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="control_locked",
                translation_placeholders={"control_mode": data.control_mode.name.lower()},
            )
        try:
            await self.coordinator.config_entry.runtime_data.client.async_update_settings(**settings)
        except FireplusApiClientError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="update_settings_failed",
                translation_placeholders={"error": str(exception)},
            ) from exception
        # the client waits until the fire+ reports the new value
        await self.coordinator.async_request_refresh()
