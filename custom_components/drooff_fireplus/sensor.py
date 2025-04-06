"""Sensor platform for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from .entity import FireplusEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FireplusDataUpdateCoordinator
    from .data import FireplusConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="drooff_fireplus_temperature",
        name="Fire+ Temperature",
        icon="mdi:gauge",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        FireplusSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class FireplusSensor(FireplusEntity, SensorEntity):
    """drooff_fireplus Sensor class."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.device_class = SensorDeviceClass.TEMPERATURE
        self.native_unit_of_measurement = "°C"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return int(self.coordinator.data[2:-1].split("\\n")[5])
