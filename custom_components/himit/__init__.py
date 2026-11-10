"""Hisense Hi-Mit II Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HimitAPI
from .const import DOMAIN
from .coordinator import HimitCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hi-Mit II from a config entry."""
    session = async_get_clientsession(hass)
    api = HimitAPI(session)
    coordinator = HimitCoordinator(hass, api, entry)

    # Initial fetch — raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_enable_periodic_sensors(hass, entry)

    # Listen for option updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


@callback
def _async_enable_periodic_sensors(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Enable only the four periodic candidates disabled by earlier defaults.

    Do not disable existing entities or override explicit user disables.
    """
    from .sensor import RAW_SENSOR_DESCRIPTIONS

    keys = {description.key for description in RAW_SENSOR_DESCRIPTIONS
            if description.entity_registry_enabled_default}
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.platform == DOMAIN
            and entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION
            and any(entity.unique_id.endswith(f"_{key}") for key in keys)
        ):
            registry.async_update_entity(entity.entity_id, disabled_by=None)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates (ignore token-only updates of entry.data)."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None and dict(entry.options) == coordinator.loaded_options:
        return
    await hass.config_entries.async_reload(entry.entry_id)
