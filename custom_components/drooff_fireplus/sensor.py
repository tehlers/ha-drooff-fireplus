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


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        [
            FireplusTemperatureSensor(entry.runtime_data.coordinator),
            FireplusDraughtSensor(entry.runtime_data.coordinator),
            FireplusAirSliderSensor(entry.runtime_data.coordinator),
        ]
    )


class FireplusTemperatureSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ combustion chamber temperature sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_temperature"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_temperature",
            name="fire+ temperature",
            icon="mdi:gauge",
        )
        self.device_class = SensorDeviceClass.TEMPERATURE
        self.native_unit_of_measurement = "°C"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.temperature


class FireplusDraughtSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ chimney draught sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the draught sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_draught"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_draught",
            name="fire+ chimney draught",
            icon="mdi:gauge",
        )
        self.device_class = SensorDeviceClass.PRESSURE
        self.native_unit_of_measurement = "Pa"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.draught


class FireplusAirSliderSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ air slider position sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the air slider position sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_air_slider"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_air_slider",
            name="fire+ air slider position",
        )
        self.native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.air_slider
