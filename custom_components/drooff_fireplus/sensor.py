"""Sensor platform for drooff_fireplus."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfMass,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)

from .api import (
    FireplusControlMode,
    FireplusError,
    FireplusFilterStatus,
    FireplusOperationStatus,
    FireplusUpdateResult,
)
from .const import ETHERNET_LINK
from .entity import FireplusEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .api import FireplusResponse, FireplusUpdateStatus
    from .coordinator import FireplusDataUpdateCoordinator
    from .data import FireplusConfigEntry
    from .statistics import FireplusStatistics

# Read-only platform, all data comes from the coordinator
PARALLEL_UPDATES = 0


def _always(_: FireplusResponse) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class FireplusSensorEntityDescription(SensorEntityDescription):
    """Describes a Drooff fire+ sensor."""

    value_fn: Callable[[FireplusResponse], StateType]
    # Whether the value is available right now
    available_fn: Callable[[FireplusResponse], bool] = _always
    # Whether the fire+ supports the value at all (enables the entity by default)
    supported_fn: Callable[[FireplusResponse], bool] = _always
    attributes_fn: Callable[[FireplusResponse], dict[str, Any]] | None = None
    unique_id_suffix: str | None = None


def _error_attributes(data: FireplusResponse) -> dict[str, Any]:
    return {"error": data.error.name, "error_code": data.error_code}


SENSORS: tuple[FireplusSensorEntityDescription, ...] = (
    FireplusSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        value_fn=lambda data: data.temperature,
        attributes_fn=lambda data: {"max_temperature": data.max_temperature},
    ),
    FireplusSensorEntityDescription(
        key="draught",
        translation_key="draught",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PA,
        suggested_display_precision=1,
        value_fn=lambda data: data.chimney_draught,
        available_fn=lambda data: data.chimney_draught_available,
    ),
    FireplusSensorEntityDescription(
        key="air_slider_position",
        translation_key="air_slider_position",
        unique_id_suffix="air_slider",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: data.air_slider,
    ),
    FireplusSensorEntityDescription(
        key="operation_status",
        translation_key="operation_status",
        device_class=SensorDeviceClass.ENUM,
        options=[status.name for status in FireplusOperationStatus],
        value_fn=lambda data: data.operation_status.name,
    ),
    FireplusSensorEntityDescription(
        key="operating_time",
        translation_key="operating_time",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data.operating_time,
        available_fn=lambda data: data.operating_time is not None,
        supported_fn=lambda data: data.operating_time is not None,
    ),
    FireplusSensorEntityDescription(
        key="heating_progress",
        translation_key="heating_progress",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: data.heating_progress,
        available_fn=lambda data: data.operation_status == FireplusOperationStatus.HEATING,
    ),
    FireplusSensorEntityDescription(
        key="error_message",
        translation_key="error_message",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=[error.name.lower() for error in FireplusError],
        value_fn=lambda data: data.error.name.lower(),
        attributes_fn=_error_attributes,
    ),
    FireplusSensorEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        value_fn=lambda data: data.target_temperature,
        available_fn=lambda data: data.target_temperature is not None,
        supported_fn=lambda data: data.target_temperature is not None,
    ),
    FireplusSensorEntityDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=1,
        value_fn=lambda data: data.weight,
        # 0 means the fire+ does not provide a recommendation
        available_fn=lambda data: data.weight is not None and data.weight > 0.0,
        supported_fn=lambda data: data.weight is not None and data.weight > 0.0,
    ),
    FireplusSensorEntityDescription(
        key="wifi_signal_strength",
        translation_key="wifi_signal_strength",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda data: data.wifi_signal_strength,
        available_fn=lambda data: data.wifi_signal_strength is not None,
        supported_fn=lambda data: data.wifi_signal_strength is not None,
    ),
    FireplusSensorEntityDescription(
        key="control_mode",
        translation_key="control_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=[mode.name.lower() for mode in FireplusControlMode],
        value_fn=lambda data: data.control_mode.name.lower() if data.control_mode else None,
        available_fn=lambda data: data.control_mode is not None,
        supported_fn=lambda data: data.control_mode is not None,
    ),
    FireplusSensorEntityDescription(
        key="filter_status",
        translation_key="filter_status",
        device_class=SensorDeviceClass.ENUM,
        options=[status.name.lower() for status in FireplusFilterStatus],
        value_fn=lambda data: data.filter_status.name.lower() if data.filter_status else None,
        available_fn=lambda data: data.filter_status is not None,
        # only stoves with the Blue Angel label have an OekoSolve filter
        supported_fn=lambda data: data.blue_angel,
        attributes_fn=lambda data: {"filter_code": data.filter_code},
    ),
    FireplusSensorEntityDescription(
        key="web_app_version",
        translation_key="web_app_version",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.web_app_version,
        available_fn=lambda data: data.web_app_version is not None,
        supported_fn=lambda data: data.web_app_version is not None,
    ),
)


@dataclass(frozen=True, kw_only=True)
class FireplusStatisticsSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor with statistics from the event log of the fire+."""

    value_fn: Callable[[FireplusStatistics], StateType | datetime]
    # Whether the fire+ supports the value at all (besides having an event log)
    supported_fn: Callable[[FireplusResponse], bool] = _always


STATISTICS_SENSORS: tuple[FireplusStatisticsSensorEntityDescription, ...] = (
    FireplusStatisticsSensorEntityDescription(
        key="fires",
        translation_key="fires",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda statistics: statistics.fires,
    ),
    FireplusStatisticsSensorEntityDescription(
        key="reloads",
        translation_key="reloads",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda statistics: statistics.reloads,
    ),
    FireplusStatisticsSensorEntityDescription(
        key="wood_consumption",
        translation_key="wood_consumption",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=1,
        value_fn=lambda statistics: statistics.wood,
        # estimated from the recommended wood load, which only recent devices provide
        supported_fn=lambda data: data.weight is not None and data.weight > 0.0,
    ),
    FireplusStatisticsSensorEntityDescription(
        key="last_reload",
        translation_key="last_reload",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda statistics: (
            datetime.fromtimestamp(statistics.last_reload, UTC) if statistics.last_reload else None
        ),
    ),
)


@dataclass(frozen=True, kw_only=True)
class FireplusUpdateSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor with the software update information of the fire+."""

    value_fn: Callable[[FireplusUpdateStatus], StateType]
    attributes_fn: Callable[[FireplusUpdateStatus], dict[str, Any]] | None = None


UPDATE_SENSORS: tuple[FireplusUpdateSensorEntityDescription, ...] = (
    FireplusUpdateSensorEntityDescription(
        key="update_result",
        translation_key="update_result",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=[result.name.lower() for result in FireplusUpdateResult],
        value_fn=lambda status: status.result.name.lower(),
        # the message of the fire+ is German only
        attributes_fn=lambda status: {"code": status.code, "message": status.message},
    ),
    FireplusUpdateSensorEntityDescription(
        key="update_schedule",
        translation_key="update_schedule",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda status: status.schedule or None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(FireplusSensor(coordinator, description) for description in SENSORS)
    async_add_entities(FireplusStatisticsSensor(coordinator, description) for description in STATISTICS_SENSORS)
    async_add_entities(FireplusUpdateSensor(coordinator, description) for description in UPDATE_SENSORS)


class FireplusSensor(FireplusEntity, SensorEntity):
    """Drooff fire+ sensor."""

    entity_description: FireplusSensorEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description, description.unique_id_suffix)
        self._attr_entity_registry_enabled_default = description.entity_registry_enabled_default and (
            description.supported_fn(coordinator.data)
        )

    @property
    def available(self) -> bool:
        """Return the availability of the sensor."""
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def native_value(self) -> StateType:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)

    @property
    def icon(self) -> str | None:
        """Return the icons that depend on the state, all other icons come from icons.json."""
        if self.entity_description.key == "operation_status":
            # icons.json only accepts lower-case states, operation_status keeps upper-case ones
            if self.coordinator.data.operation_status == FireplusOperationStatus.STANDBY:
                return "mdi:fireplace-off"
            return super().icon
        if self.entity_description.key != "wifi_signal_strength":
            return super().icon
        bars = self.coordinator.data.wifi_signal_strength
        if bars is not None and 0 < bars < ETHERNET_LINK:
            return f"mdi:wifi-strength-{bars}"
        return "mdi:wifi-off"


class FireplusStatisticsSensor(FireplusEntity, SensorEntity):
    """Sensor with statistics from the event log of the fire+."""

    entity_description: FireplusStatisticsSensorEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusStatisticsSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        self._attr_entity_registry_enabled_default = coordinator.events_supported is not False and (
            description.supported_fn(coordinator.data)
        )

    @property
    def available(self) -> bool:
        """Return the availability of the sensor."""
        return super().available and self.coordinator.events_supported is True

    @property
    def native_value(self) -> StateType | datetime:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.statistics)


class FireplusUpdateSensor(FireplusEntity, SensorEntity):
    """Sensor with the software update information of the fire+."""

    entity_description: FireplusUpdateSensorEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusUpdateSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)

    async def async_added_to_hass(self) -> None:
        """Read the update status as long as the sensor is enabled."""
        await super().async_added_to_hass()
        self.coordinator.update_sensors += 1
        if self.coordinator.update_status is None:
            await self.coordinator.async_update_update_status()

    async def async_will_remove_from_hass(self) -> None:
        """Stop reading the update status when no sensor needs it."""
        self.coordinator.update_sensors -= 1
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        """Return the availability of the sensor."""
        return super().available and self.coordinator.update_status is not None

    @property
    def native_value(self) -> StateType:
        """Return the native value of the sensor."""
        status = self.coordinator.update_status
        return self.entity_description.value_fn(status) if status else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        status = self.coordinator.update_status
        if self.entity_description.attributes_fn is None or status is None:
            return None
        return self.entity_description.attributes_fn(status)
