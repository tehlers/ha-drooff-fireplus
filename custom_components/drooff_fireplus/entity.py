"""FireplusEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import FireplusDataUpdateCoordinator


class FireplusEntity(CoordinatorEntity[FireplusDataUpdateCoordinator]):
    """FireplusEntity class."""

    _attr_attribution = ATTRIBUTION

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
        )
