"""Check translation coverage and unchanged identity for all platforms."""
import json
from pathlib import Path

from custom_components.himit.binary_sensor import BINARY_SENSOR_DESCRIPTIONS, EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS
from custom_components.himit.sensor import SENSOR_DESCRIPTIONS, RAW_SENSOR_DESCRIPTIONS
from custom_components.himit.switch import SWITCH_DESCRIPTIONS, HimitSwitch
from custom_components.himit.number import NUMBER_DESCRIPTIONS, HimitNumber
from types import SimpleNamespace


def test_translation_coverage_and_config_flow():
    root = Path(__file__).parents[1] / "custom_components/himit/translations"
    descriptions = {
        "binary_sensor": (*BINARY_SENSOR_DESCRIPTIONS, *EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS),
        "sensor": (*SENSOR_DESCRIPTIONS, *RAW_SENSOR_DESCRIPTIONS),
        "switch": SWITCH_DESCRIPTIONS, "number": NUMBER_DESCRIPTIONS,
    }
    for lang in ("en", "pl"):
        data = json.loads((root / f"{lang}.json").read_text(encoding="utf-8"))
        for platform, items in descriptions.items():
            for desc in items:
                assert desc.translation_key == desc.key
                name = data["entity"][platform][desc.translation_key]["name"]
                assert isinstance(name, str) and name
        assert set(data["config"]["step"]) == {"user", "home", "reauth_confirm", "reconfigure"}
        assert "scan_interval" in data["options"]["step"]["init"]["data"]


def test_control_entity_identity_is_preserved():
    coord = SimpleNamespace(data={"test-device": {}}, last_update_success=True)
    assert [desc.key for desc in SWITCH_DESCRIPTIONS] == ["circuit1", "circuit2", "dhw", "swp"]
    assert [desc.key for desc in NUMBER_DESCRIPTIONS] == ["c1_setpoint", "c2_setpoint", "dhw_setpoint", "swp_setpoint"]
    for cls, items in ((HimitSwitch, SWITCH_DESCRIPTIONS), (HimitNumber, NUMBER_DESCRIPTIONS)):
        for desc in items:
            entity = cls(coord, "test-device", desc)
            assert entity.unique_id == f"test-device_{desc.key}"
            assert entity.device_info["identifiers"] == {("himit", "test-device")}
