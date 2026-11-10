"""Migrate integration-disabled diagnostics without overriding user choices."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from custom_components.himit import _async_enable_periodic_sensors


def test_enable_only_periodic_candidates_disabled_by_integration():
    def row(key, reason, platform="himit"):
        return SimpleNamespace(entity_id=f"sensor.{key}", unique_id=f"device_{key}",
                               platform=platform, disabled_by=reason)
    entries = [
        row("defrost_spaceheat", RegistryEntryDisabler.INTEGRATION),
        row("run_mode_raw", RegistryEntryDisabler.INTEGRATION),
        row("telemetry_fd_raw", RegistryEntryDisabler.INTEGRATION),
        row("silent_mode", RegistryEntryDisabler.USER),
        row("eco_mode", None),
        row("c1_setpoint", RegistryEntryDisabler.INTEGRATION),
        row("defrost_dhw", RegistryEntryDisabler.INTEGRATION, "other"),
        row("telemetry_power_heating_raw", RegistryEntryDisabler.INTEGRATION),
        row("telemetry_capacity_heating_raw", RegistryEntryDisabler.INTEGRATION),
        row("telemetry_power_dhw_raw", RegistryEntryDisabler.INTEGRATION),
        row("telemetry_capacity_dhw_raw", RegistryEntryDisabler.INTEGRATION),
        row("telemetry_power_heating_raw", RegistryEntryDisabler.USER),
        row("telemetry_capacity_heating_raw", None),
        row("telemetry_power_dhw_raw", RegistryEntryDisabler.INTEGRATION, "other"),
    ]
    registry = Mock()
    with patch("custom_components.himit.er.async_get", return_value=registry), patch(
        "custom_components.himit.er.async_entries_for_config_entry", return_value=entries
    ):
        _async_enable_periodic_sensors(object(), SimpleNamespace(entry_id="entry"))
    assert registry.async_update_entity.call_count == 4
    assert {call.args[0] for call in registry.async_update_entity.call_args_list} == {
        "sensor.telemetry_power_heating_raw", "sensor.telemetry_capacity_heating_raw",
        "sensor.telemetry_power_dhw_raw", "sensor.telemetry_capacity_dhw_raw",
    }
    assert all(call.kwargs == {"disabled_by": None} for call in registry.async_update_entity.call_args_list)
