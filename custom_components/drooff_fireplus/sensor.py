"""Sensor platform for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)

from .api import FireplusOperationMode
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
            FireplusOperationModeSensor(entry.runtime_data.coordinator),
            FireplusOperatingTimeSensor(entry.runtime_data.coordinator),
            FireplusHeatingProgressSensor(entry.runtime_data.coordinator),
            FireplusErrorMessageSensor(entry.runtime_data.coordinator),
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
        self.native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.temperature

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes related to the temperature sensor."""
        return {"max_temperature": self.coordinator.data.max_temperature}


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
        self.native_unit_of_measurement = UnitOfPressure.PA

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
        self.native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.air_slider


class FireplusOperationModeSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ operation mode sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the operation mode sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_operation_mode"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_operation_mode",
            name="fire+ operation mode",
        )
        self.device_class = SensorDeviceClass.ENUM
        self.options = [om.name for om in FireplusOperationMode]

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.operation_mode.name

    @property
    def icon(self) -> str:
        """Return icon that represents the state of the fireplace."""
        return (
            "mdi:fireplace-off"
            if self.coordinator.data.operation_mode == FireplusOperationMode.STANDBY
            else "mdi:fireplace"
        )


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
        self.native_unit_of_measurement = UnitOfTime.SECONDS

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.operating_time


class FireplusHeatingProgressSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ heating progress sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the heating progress sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_heating_progress"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_heating_progress",
            name="fire+ heating progress",
            icon="mdi:progress-helper",
        )
        self.native_unit_of_measurement = PERCENTAGE

    @property
    def available(self) -> bool | None:
        """Return the availability of the sensor."""
        return self.coordinator.data.operation_mode == FireplusOperationMode.HEATING

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.heating_progress


class FireplusErrorMessageSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ error message sensor."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the error message sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_error_message"
        self.entity_description = SensorEntityDescription(
            key="drooff_fireplus_error_message",
            name="fire+ error message",
            icon="mdi:alert",
            translation_key="error_message",
            has_entity_name=True,
        )

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.error.name.lower()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes related to the error message."""
        return {
            "error": self.coordinator.data.error.name,
            "error_code": self.coordinator.data.error_code,
        }
