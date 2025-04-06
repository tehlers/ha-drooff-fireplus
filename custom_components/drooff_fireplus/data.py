"""Custom types for drooff_fireplus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import FireplusApiClient
    from .coordinator import FireplusDataUpdateCoordinator


type FireplusConfigEntry = ConfigEntry[FireplusData]


@dataclass
class FireplusData:
    """Data for the Fireplus integration."""

    client: FireplusApiClient
    coordinator: FireplusDataUpdateCoordinator
    integration: Integration
