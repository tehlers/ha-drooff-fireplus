"""Switch platform for drooff_fireplus."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

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
    """Set up the switch platform."""
    async_add_entities(
        [
            FireplusEmberBurndownSwitch(entry.runtime_data.coordinator),
            FireplusLedSwitch(entry.runtime_data.coordinator),
        ]
    )


class FireplusEmberBurndownSwitch(FireplusEntity, SwitchEntity):
    """Switch to toggle between ember preservation and ember burndown."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_ember_burndown"
        self.entity_description = SwitchEntityDescription(
            key="ember_burndown", translation_key="ember_burndown", has_entity_name=True
        )

    @property
    def icon(self) -> str:
        """Return icon that represents the state of the switch."""
        return "mdi:toggle-switch" if self.is_on else "mdi:toggle-switch-off"

    @property
    def is_on(self) -> bool:
        """Return true if ember burndown is on."""
        return self.coordinator.data.ember_burndown

    async def async_turn_on(self, **_: Any) -> None:
        """Activate ember burndown."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(ember_burndown=True)
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Activate ember preservation."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(ember_burndown=False)
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()


class FireplusLedSwitch(FireplusEntity, SwitchEntity):
    """Switch to toggle LED."""

    def __init__(
        self,
        coordinator: FireplusDataUpdateCoordinator,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id + "_led"
        self.entity_description = SwitchEntityDescription(key="led", translation_key="led", has_entity_name=True)

    @property
    def icon(self) -> str:
        """Return icon that represents the state of the switch."""
        return "mdi:toggle-switch" if self.is_on else "mdi:toggle-switch-off"

    @property
    def is_on(self) -> bool:
        """Return true if led is on."""
        return self.coordinator.data.led

    async def async_turn_on(self, **_: Any) -> None:
        """Activate led."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(led=True)
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Deactivate led."""
        await self.coordinator.config_entry.runtime_data.client.async_update_settings(led=False)
        # Give fire+ time to update value
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool | None:
        """Return the availability of the switch."""
        return self.coordinator.data.led is not None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return self.available
