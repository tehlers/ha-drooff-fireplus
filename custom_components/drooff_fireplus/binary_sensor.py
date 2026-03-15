"""Binary sensor platform for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory

from .api import FireplusError
from .entity import FireplusEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FireplusDataUpdateCoordinator
    from .data import FireplusConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        [
            FireplusErrorSensor(entry.runtime_data.coordinator),
            FireplusDoorSensor(entry.runtime_data.coordinator),
        ]
    )


class FireplusErrorSensor(FireplusEntity, BinarySensorEntity):
    """Drooff fire+ error sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_error"
        self.entity_description = BinarySensorEntityDescription(
            key="error",
            translation_key="error",
            has_entity_name=True,
            icon="mdi:alert",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self.device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        """Return true if the fire+ signals an error."""
        return self.coordinator.data.error != FireplusError.NONE

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes related to the error."""
        return {
            "error": self.coordinator.data.error.name,
            "error_code": self.coordinator.data.error_code,
        }

class FireplusDoorSensor(FireplusEntity, BinarySensorEntity):
    """Drooff fire+ door sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_door_open"
        self.entity_description = BinarySensorEntityDescription(
            key="door_open",
            translation_key="door_open",
            has_entity_name=True,
            icon="mdi:door",
        )
        self.device_class = BinarySensorDeviceClass.DOOR

    @property
    def is_on(self) -> bool:
        """Return true if the fire+ door is open."""
        return self.coordinator.data.door_open