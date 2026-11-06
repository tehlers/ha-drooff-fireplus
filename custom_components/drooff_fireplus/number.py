"""Number platform for drooff_fireplus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory

from .api import VERSION_2_0_0
from .entity import FireplusEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import FireplusResponse
    from .coordinator import FireplusDataUpdateCoordinator
    from .data import FireplusConfigEntry

# The fire+ accepts only one settings write at a time
PARALLEL_UPDATES = 1

LOW_VOLUME = 30
MEDIUM_VOLUME = 70


def _always(_: FireplusResponse) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class FireplusNumberEntityDescription(NumberEntityDescription):
    """Describes a Drooff fire+ number."""

    value_fn: Callable[[FireplusResponse], float | None]
    # Name of the keyword argument of FireplusApiClient.async_update_settings
    setting: str
    available_fn: Callable[[FireplusResponse], bool] = _always
    max_fn: Callable[[FireplusResponse], float] | None = None


NUMBERS: tuple[FireplusNumberEntityDescription, ...] = (
    FireplusNumberEntityDescription(
        key="burn_rate",
        translation_key="burn_rate",
        mode=NumberMode.SLIDER,
        native_min_value=1.0,
        native_step=1.0,
        value_fn=lambda data: data.burn_rate,
        setting="burn_rate",
        # firmware 1.x has 7 stages, 2.x has 6
        max_fn=lambda data: 6.0 if data.version >= VERSION_2_0_0 else 7.0,
    ),
    FireplusNumberEntityDescription(
        key="brightness",
        translation_key="brightness",
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.SLIDER,
        native_step=10.0,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.brightness,
        setting="brightness",
    ),
    FireplusNumberEntityDescription(
        key="volume",
        translation_key="volume",
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.SLIDER,
        native_step=10.0,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.volume,
        setting="volume",
        available_fn=lambda data: data.volume is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(FireplusNumber(coordinator, description) for description in NUMBERS)


class FireplusNumber(FireplusEntity, NumberEntity):
    """Drooff fire+ number."""

    entity_description: FireplusNumberEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusNumberEntityDescription,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator, description)
        self._attr_entity_registry_enabled_default = description.available_fn(coordinator.data)

    @property
    def available(self) -> bool:
        """Return the availability of the number."""
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def native_value(self) -> float | None:
        """Return the native value of the entity."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def native_max_value(self) -> float:
        """Return the maximal native value of the entity."""
        if self.entity_description.max_fn is not None:
            return self.entity_description.max_fn(self.coordinator.data)
        return super().native_max_value

    @property
    def icon(self) -> str | None:
        """Return the volume icon by level, all other icons come from icons.json."""
        if self.entity_description.key != "volume":
            return super().icon
        volume = self.native_value
        if not volume:
            return "mdi:volume-off"
        if volume <= LOW_VOLUME:
            return "mdi:volume-low"
        if volume <= MEDIUM_VOLUME:
            return "mdi:volume-medium"
        return "mdi:volume-high"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self._async_update_settings(**{self.entity_description.setting: int(value)})
