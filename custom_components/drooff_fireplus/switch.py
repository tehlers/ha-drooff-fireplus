"""Switch platform for drooff_fireplus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

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


def _always(_: FireplusResponse) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class FireplusSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Drooff fire+ switch."""

    is_on_fn: Callable[[FireplusResponse], bool | None]
    # Name of the keyword argument of FireplusApiClient.async_update_settings
    setting: str
    available_fn: Callable[[FireplusResponse], bool] = _always


SWITCHES: tuple[FireplusSwitchEntityDescription, ...] = (
    FireplusSwitchEntityDescription(
        key="ember_burndown",
        translation_key="ember_burndown",
        is_on_fn=lambda data: data.ember_burndown,
        setting="ember_burndown",
    ),
    FireplusSwitchEntityDescription(
        key="led",
        translation_key="led",
        is_on_fn=lambda data: data.led,
        setting="led",
        # only firmware 1.x can switch the LED
        available_fn=lambda data: data.led is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(FireplusSwitch(coordinator, description) for description in SWITCHES)


class FireplusSwitch(FireplusEntity, SwitchEntity):
    """Drooff fire+ switch."""

    entity_description: FireplusSwitchEntityDescription

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
        description: FireplusSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description)
        self._attr_entity_registry_enabled_default = description.available_fn(coordinator.data)

    @property
    def available(self) -> bool:
        """Return the availability of the switch."""
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **_: Any) -> None:
        """Turn the switch on."""
        await self._async_update_settings(**{self.entity_description.setting: True})

    async def async_turn_off(self, **_: Any) -> None:
        """Turn the switch off."""
        await self._async_update_settings(**{self.entity_description.setting: False})
