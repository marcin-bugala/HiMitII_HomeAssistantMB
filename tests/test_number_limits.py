"""Regression coverage for the requested fixed Circuit 1 minimum."""
from types import SimpleNamespace

import pytest

from custom_components.himit.number import HimitNumber, NUMBER_DESCRIPTIONS


@pytest.mark.parametrize("reported_min", [None, 12.0, 21.0, 27.0, "27"])
def test_circuit1_minimum_is_fixed_at_20(reported_min):
    coordinator = SimpleNamespace(data={"device": {
        "fixedDid27": reported_min, "fixedDid28": 35.0,
    }})
    description = next(item for item in NUMBER_DESCRIPTIONS if item.key == "c1_setpoint")
    entity = HimitNumber(coordinator, "device", description)
    assert entity.native_min_value == 20.0
    assert entity.native_max_value == 35.0


def test_circuit2_keeps_device_reported_minimum():
    coordinator = SimpleNamespace(data={"device": {"fixedDid27": 27.0}})
    description = next(item for item in NUMBER_DESCRIPTIONS if item.key == "c2_setpoint")
    assert HimitNumber(coordinator, "device", description).native_min_value == 27.0
