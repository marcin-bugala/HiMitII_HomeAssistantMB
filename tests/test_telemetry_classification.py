"""Recorded variation supports prioritization, not calibrated engineering units."""
from types import SimpleNamespace
from custom_components.himit.sensor import RAW_SENSOR_DESCRIPTIONS, HimitSensor
from custom_components.himit.telemetry import PERIODIC_FIELDS


def test_four_periodic_candidates_preserve_raw_values_and_identity():
    assert PERIODIC_FIELDS == {"Power_heating", "Capacity_heating", "Power_DHW", "Capacity_DHW"}
    for desc in RAW_SENSOR_DESCRIPTIONS:
        if desc.field not in PERIODIC_FIELDS:
            continue
        coord = SimpleNamespace(data={"device": {desc.field: "7"}}, last_update_success=True)
        entity = HimitSensor(coord, "device", desc)
        assert entity.native_value == "7"  # not 0.7 kWh or 7 kW
        assert entity.unique_id == f"device_{desc.key}"
        assert desc.native_unit_of_measurement is None
        assert desc.state_class is None
        assert desc.device_class is None
        assert entity.extra_state_attributes["source_field"] == desc.field
        assert entity.extra_state_attributes["mapping_confidence"] == "raw_unmapped"
        assert entity.extra_state_attributes["period_verified"] is False
        assert entity.extra_state_attributes["unit_scale_verified"] is False


def test_all_30_additions_remain_available_for_manual_observation():
    from custom_components.himit.binary_sensor import EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS
    assert len(EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS) + len(RAW_SENSOR_DESCRIPTIONS) == 30
    assert sum(d.entity_registry_enabled_default for d in RAW_SENSOR_DESCRIPTIONS) == 4
    assert not any(d.entity_registry_enabled_default for d in EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS)
