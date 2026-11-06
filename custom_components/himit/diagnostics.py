"""Diagnostics support for Hisense Hi-Mit II."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .privacy import redact_diagnostics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Token lifecycle info (non-sensitive)
    token_info = {
        "token_created_ms": entry.data.get("token_created_ms", 0),
        "token_expire_secs": entry.data.get("token_expire_secs", 0),
        "refresh_expire_secs": entry.data.get("refresh_expire_secs", 0),
        "token_is_expiring": coordinator._token_is_expiring(),
        "refresh_token_is_valid": coordinator._refresh_token_is_valid(),
    }

    # Discovered devices (redact sensitive fields)
    devices = [
        redact_diagnostics(d)
        for d in coordinator.atw_devices
    ]

    # Raw discovery response (redact sensitive fields)
    raw_discovery = redact_diagnostics(coordinator._raw_device_discovery)

    # Current coordinator data (device states)
    device_states = {}
    if coordinator.data:
        for index, state in enumerate(coordinator.data.values(), start=1):
            device_states[f"device_{index}"] = redact_diagnostics(state)

    return {
        "config_entry": redact_diagnostics(dict(entry.data)),
        "options": redact_diagnostics(dict(entry.options)),
        "token_lifecycle": token_info,
        "discovered_devices": devices,
        "raw_device_discovery": raw_discovery,
        "device_states": device_states,
        "update_interval_seconds": coordinator.update_interval.total_seconds()
        if coordinator.update_interval
        else None,
        "last_update_success": coordinator.last_update_success,
    }
