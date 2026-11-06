"""Binary sensor platform for drooff_fireplus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .api import FILTER_PROBLEMS, FireplusError
from .entity import FireplusEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import FireplusResponse
    from .coordinator import FireplusDataUpdateCoordinator
    from .data import FireplusConfigEntry

# Read-only platform, all data comes from the coordinator
PARALLEL_UPDATES = 0


def _always(_: FireplusResponse) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class FireplusBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Drooff fire+ binary sensor."""

    is_on_fn: Callable[[FireplusResponse], bool | None]
    # State kept by the coordinator instead of a value of the fire+
    coordinator_is_on_fn: Callable[[FireplusDataUpdateCoordinator], bool | None] | None = None
    available_fn: Callable[[FireplusResponse], bool] = _always
    supported_fn: Callable[[FireplusResponse], bool] = _always
    attributes_fn: Callable[[FireplusResponse], dict[str, Any]] | None = None


BINARY_SENSORS: tuple[FireplusBinarySensorEntityDescription, ...] = (
    FireplusBinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.error != FireplusError.NONE,
        attributes_fn=lambda data: {"error": data.error.name, "error_code": data.error_code},
    ),
    FireplusBinarySensorEntityDescription(
        key="door_open",
        translation_key="door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: data.door_open,
        available_fn=lambda data: data.door_open is not None,
        supported_fn=lambda data: data.door_open is not None,
    ),
    FireplusBinarySensorEntityDescription(
        key="door_open_too_long",
        translation_key="door_open_too_long",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda _: None,
        coordinator_is_on_fn=lambda coordinator: coordinator.door_open_too_long,
        available_fn=lambda data: data.door_open is not None,
        supported_fn=lambda data: data.door_open is not None,
    ),
    FireplusBinarySensorEntityDescription(
        key="filter_problem",
        translation_key="filter_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda data: data.filter_status in FILTER_PROBLEMS if data.filter_status else None,
        available_fn=lambda data: data.filter_status is not None,
        supported_fn=lambda data: data.blue_angel,
    ),
    FireplusBinarySensorEntityDescription(
        key="ethernet_link",
        translation_key="ethernet_link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.ethernet_link,
        available_fn=lambda data: data.ethernet_link is not None,
        supported_fn=lambda data: data.ethernet_link is not None,
    ),
    FireplusBinarySensorEntityDescription(
        key="online_support",
        translation_key="online_support",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.online_support,
        available_fn=lambda data: data.online_support is not None,
        supported_fn=lambda data: data.online_support is not None,
    ),
    FireplusBinarySensorEntityDescription(
        key="auto_update",
        translation_key="auto_update",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.auto_update,
        available_fn=lambda data: data.auto_update is not None,
        supported_fn=lambda data: data.auto_update is not None,
    ),
    FireplusBinarySensorEntityDescription(
        key="draught_warning",
        translation_key="draught_warning",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.draught_warning,
        available_fn=lambda data: data.draught_warning is not None,
        supported_fn=lambda data: data.draught_warning is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(FireplusBinarySensor(coordinator, description) for description in BINARY_SENSORS)


class FireplusBinarySensor(FireplusEntity, BinarySensorEntity):
    """Drooff fire+ binary sensor."""

    entity_description: FireplusBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description)
        self._attr_entity_registry_enabled_default = description.supported_fn(coordinator.data)

    @property
    def available(self) -> bool:
        """Return the availability of the binary sensor."""
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        if self.entity_description.coordinator_is_on_fn is not None:
            return self.entity_description.coordinator_is_on_fn(self.coordinator)
        return self.entity_description.is_on_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)
