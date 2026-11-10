"""Offline regression tests using real HA entity classes and sanitized telemetry."""
import asyncio
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.himit.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS, EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS,
    HimitBinarySensor, async_setup_entry as setup_binary,
)
from custom_components.himit.sensor import (
    SENSOR_DESCRIPTIONS, RAW_SENSOR_DESCRIPTIONS, HimitSensor,
    async_setup_entry as setup_sensor,
)
from custom_components.himit.coordinator import _parse_property
from custom_components.himit.diagnostics import async_get_config_entry_diagnostics
from custom_components.himit.telemetry import binary_value, raw_value
from custom_components.himit.telemetry import PERIODIC_FIELDS


@pytest.fixture
def state():
    return json.loads((Path(__file__).parent / "fixtures/cloud_state.json").read_text(encoding="utf-8-sig"))


def coordinator(state):
    return SimpleNamespace(data={"test-device": state}, last_update_success=True)


@pytest.mark.parametrize("value,expected", [
    ("0", False), ("1", True), (False, False), (True, True),
    (0, False), (1, True), (0.0, False), (1.0, True),
    (" false ", False), ("TRUE", True), (None, None), ("", None),
    ("null", None), ("2", None), (2, None), (-1, None),
    ([], None), ({}, None), (float("nan"), None), ("00", None),
])
def test_binary_decoder(value, expected):
    assert binary_value(value) is expected


@pytest.mark.parametrize("value,expected", [
    ("00", "00"), (0, "0"), (0.0, "0.0"), ("A03", "A03"),
    ("unknown-code", "unknown-code"), (None, None), (False, None),
    ({}, None), ([], None), ("null", None), ("nan", None),
    (float("inf"), None), ("\0" + "0", None), ("a" * 256, None),
])
def test_raw_decoder(value, expected):
    assert raw_value(value) == expected


def test_snapshot_and_entity_updates(state):
    before = copy.deepcopy(state)
    coord = coordinator(state)
    for desc in EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS:
        assert desc.field in state
        entity = HimitBinarySensor(coord, "test-device", desc)
        assert entity.is_on is False
        assert entity.available
        assert not desc.entity_registry_enabled_default
        assert desc.entity_category is EntityCategory.DIAGNOSTIC
        assert entity.extra_state_attributes["mapping_confidence"] == "experimental"
        coord.data = {"test-device": {desc.field: "1"}}
        assert entity.is_on is True
        coord.data = {"test-device": {desc.field: "unexpected"}}
        assert entity.is_on is None and not entity.available
        coord.data = {"test-device": {}}
        assert not entity.available
        coord.data = {}
        assert not entity.available
        coord.data = {"test-device": state}
        coord.last_update_success = False
        assert not entity.available
        coord.last_update_success = True
    for desc in RAW_SENSOR_DESCRIPTIONS:
        assert desc.field in state
        entity = HimitSensor(coord, "test-device", desc)
        assert entity.available
        assert entity.native_value == str(state[desc.field])
        assert desc.native_unit_of_measurement is None
        assert desc.state_class is None
        assert desc.device_class is None
        assert desc.entity_registry_enabled_default == (desc.field in PERIODIC_FIELDS)
        assert desc.entity_category == (None if desc.field in PERIODIC_FIELDS else EntityCategory.DIAGNOSTIC)
        assert entity.extra_state_attributes["suitable_for_realtime_control"] is False
        assert entity.extra_state_attributes["data_role"] == (
            "periodic_unverified" if desc.field in PERIODIC_FIELDS else "auxiliary_unverified"
        )
        coord.data = {"test-device": {desc.field: "A03"}}
        assert entity.native_value == "A03"
        coord.data = {"test-device": {}}
        assert not entity.available
        coord.data = {"test-device": state}
        coord.last_update_success = False
        assert not entity.available
        coord.last_update_success = True
    assert state == before


def test_legacy_entity_identity_and_values(state):
    coord = coordinator(state)
    legacy_keys = ["c1_water_actual", "c2_water_actual", "dhw_water_actual",
                   "swp_water_actual", "outdoor_temp", "c1_setpoint", "c2_setpoint",
                   "dhw_setpoint", *[f"room_temp_r{i}" for i in range(1, 9)]]
    assert [desc.key for desc in SENSOR_DESCRIPTIONS] == legacy_keys
    for desc in SENSOR_DESCRIPTIONS:
        entity = HimitSensor(coord, "test-device", desc)
        assert entity.unique_id == f"test-device_{desc.key}"
        assert entity.native_value == state[desc.field]
        if desc.key.startswith("room_temp_r"):
            assert entity.extra_state_attributes["measurement_verified"] is False
            assert not desc.entity_registry_enabled_default
        else:
            assert entity.extra_state_attributes is None
    legacy = HimitBinarySensor(coord, "test-device", BINARY_SENSOR_DESCRIPTIONS[0])
    assert legacy.unique_id == "test-device_a2w_running"
    assert legacy.entity_description.translation_key == "a2w_running"
    assert legacy.is_on is True
    assert legacy.extra_state_attributes["data_role"] == "unit_enabled"
    assert legacy.extra_state_attributes["compressor_running_verified"] is False
    assert legacy.entity_description.device_class is None


def test_parser_precedence_and_legacy_readings():
    parsed = _parse_property({
        "allStatus": {"Defrost_DHW_s": "0", "realRunMode": "2", "fixedDid18": "20"},
        "functions": {"Defrost_DHW_s": "1", "realRunMode": "1"},
        "status": {"realRunMode": "0", "fixedDid18": "38", "A2W_SW_ON": "1"},
    })
    assert parsed["Defrost_DHW_s"] == "1"
    assert parsed["realRunMode"] == "0"
    assert parsed["fixedDid18"] == 38.0
    assert parsed["A2W_SW_ON"] is True
    assert parsed["fixedDid19"] is None


def test_setup_creates_unique_read_only_entities_without_api_calls(state):
    coord = coordinator(state)
    coord.async_set_property = AsyncMock(side_effect=AssertionError("No writes allowed"))
    coord.async_set_multiple = AsyncMock(side_effect=AssertionError("No writes allowed"))
    coord.api = SimpleNamespace(get_device_property=AsyncMock(side_effect=AssertionError("No extra reads")))
    hass = SimpleNamespace(data={"himit": {"entry": coord}})
    entry = SimpleNamespace(entry_id="entry")
    entities = []
    asyncio.run(setup_binary(hass, entry, entities.extend))
    asyncio.run(setup_sensor(hass, entry, entities.extend))
    assert len(entities) == 47  # 17 legacy + 30 additions
    assert len({entity.unique_id for entity in entities}) == len(entities)
    assert {desc.field for desc in RAW_SENSOR_DESCRIPTIONS if desc.entity_registry_enabled_default} == PERIODIC_FIELDS
    for entity in entities:
        assert not hasattr(entity, "async_turn_on")
        assert not hasattr(entity, "async_set_native_value")
    coord.async_set_property.assert_not_called()
    coord.async_set_multiple.assert_not_called()
    coord.api.get_device_property.assert_not_called()


def test_diagnostics_redacts_nested_identifiers_without_mutating(state):
    secrets = {
        "username": "secret-email", "password": "secret-password",
        "access_token": "secret-token", "refresh_token": "secret-refresh",
        "home_id": "secret-home", "wifiId": "secret-wifi", "deviceId": "secret-device",
        "_wifiId": "secret-internal-wifi", "_deviceId": "secret-internal-device",
        "_name": "secret-name", "bindId": "secret-bind", "serialNumber": "secret-serial",
        "floorId": "secret-floor", "roomId": "secret-room", "homeName": "secret-home-name",
    }
    entry = SimpleNamespace(entry_id="entry", data=secrets, options={})
    coord = coordinator({**state, **secrets})
    coord.data = {"secret-map-key": coord.data["test-device"]}
    coord.atw_devices = [{"nested": [secrets]}]
    coord._raw_device_discovery = {"atwInfoList": [{"nested": [secrets]}]}
    coord._token_is_expiring = lambda: False
    coord._refresh_token_is_valid = lambda: True
    coord.update_interval = None
    before = copy.deepcopy(coord.data)
    exported = asyncio.run(async_get_config_entry_diagnostics(SimpleNamespace(data={"himit": {"entry": coord}}), entry))
    serialized = json.dumps(exported)
    for secret in [*secrets.values(), "secret-map-key"]:
        assert secret not in serialized
    assert exported["device_states"]["device_1"]["Defrost_DHW_s"] == "0"
    assert coord.data == before
