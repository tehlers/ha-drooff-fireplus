"""Sensor platform for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
            FireplusChimneyDraughtSensor(entry.runtime_data.coordinator),
            FireplusAirSliderSensor(entry.runtime_data.coordinator),
            FireplusOperatingTimeSensor(entry.runtime_data.coordinator),
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


class FireplusChimneyDraughtSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ chimney draught sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the chimney draught sensor."""
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
    def available(self) -> bool | None:
        """Return the availability of the sensor."""
        return self.coordinator.data.chimney_draught_available

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.chimney_draught


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
            icon="mdi:tune",
        )
        self.native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.air_slider


class FireplusOperatingTimeSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ operating time sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the draught sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_operating_time"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_operating_time",
            name="fire+ operating time",
            icon="mdi:history",
        )
        self.device_class = SensorDeviceClass.DURATION
        self.state_class = SensorStateClass.TOTAL_INCREASING
        self.native_unit_of_measurement = "s"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.operating_time
