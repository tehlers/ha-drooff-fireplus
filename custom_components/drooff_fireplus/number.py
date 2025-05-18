"""Sensor platform for drooff_fireplus."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE

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
    """Set up the number platform."""
    async_add_entities(
        [
            FireplusBurnRate(entry.runtime_data.coordinator),
            FireplusBrightness(entry.runtime_data.coordinator),
            FireplusVolume(entry.runtime_data.coordinator),
        ]
    )


class FireplusBrightness(FireplusEntity, NumberEntity):
    """Drooff fire+ LED brightness."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the volume entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_brightness"
        self.entity_description = NumberEntityDescription(
            key="brightness",
            name="fire+ LED brightness",
            icon="mdi:led-strip",
        )
        self.mode = NumberMode.SLIDER
        self.native_step = 10.0
        self.native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the native value of the entity."""
        return self.coordinator.data.brightness

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(brightness=int(value))
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()


class FireplusVolume(FireplusEntity, NumberEntity):
    """Drooff fire+ volume."""

    LOW_VOLUME = 30
    MEDIUM_VOLUME = 70

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the volume entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_volume"
        self.entity_description = NumberEntityDescription(
            key="volume",
            name="fire+ volume",
        )
        self.mode = NumberMode.SLIDER
        self.native_step = 10.0
        self.native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the native value of the entity."""
        return self.coordinator.data.volume

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(volume=int(value))
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    @property
    def icon(self) -> str:
        """Return icon that changes based on the current volume."""
        if self.native_value == 0:
            return "mdi:volume-off"
        if self.native_value <= FireplusVolume.LOW_VOLUME:
            return "mdi:volume-low"
        if self.native_value <= FireplusVolume.MEDIUM_VOLUME:
            return "mdi:volume-medium"
        return "mdi:volume-high"


class FireplusBurnRate(FireplusEntity, NumberEntity):
    """Drooff fire+ burn rate."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the volume entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_burn_rate"
        self.entity_description = NumberEntityDescription(
            key="burn_rate",
            name="fire+ burn rate",
            icon="mdi:fire",
        )
        self.mode = NumberMode.SLIDER
        self.native_step = 1.0
        self.native_min_value = 1.0
        self.native_max_value = 6.0

    @property
    def native_value(self) -> float | None:
        """Return the native value of the entity."""
        return self.coordinator.data.burn_rate

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(burn_rate=int(value))
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
