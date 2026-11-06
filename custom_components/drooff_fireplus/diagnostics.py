"""Diagnostics support for drooff_fireplus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.const import CONF_HOST

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import FireplusResponse
    from .data import FireplusConfigEntry

TO_REDACT = {CONF_HOST, "serial_number", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: FireplusConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data
    values: dict[str, Any] = {}
    if data is not None:
        values = {
            key: (value.name if hasattr(value, "name") else str(value) if key == "version" else value)
            for key, value in vars(data).items()
            if not key.startswith("_")
        }
    return {
        "entry": async_redact_data({"data": dict(entry.data), "unique_id": entry.unique_id}, TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "update_interval": str(coordinator.update_interval),
        "data": async_redact_data(values, TO_REDACT),
        "raw_responses": _redact_raw(data),
    }


def _redact_raw(data: FireplusResponse | None) -> list[str] | None:
    """Return the raw responses without the serial number."""
    if data is None:
        return None
    serial_number = str(data.serial_number)
    return [raw.replace(serial_number, REDACTED) if serial_number else raw for raw in data.raw]
