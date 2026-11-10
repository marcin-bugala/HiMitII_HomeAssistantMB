"""Conservative decoding of unverified cloud telemetry (no control commands)."""
from __future__ import annotations

import math
from typing import Any

# These fields varied during the 6-10 Nov 2026 observation. Period/scale are
# still hypotheses, so their raw values must not be converted to power/energy.
PERIODIC_FIELDS = frozenset({
    "Power_heating", "Capacity_heating", "Power_DHW", "Capacity_DHW",
})


def binary_value(value: Any) -> bool | None:
    """Accept explicit binary values only; never treat the string '0' as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("0", "false"):
            return False
        if normalized in ("1", "true"):
            return True
    return None


def raw_value(value: Any) -> str | None:
    """Expose scalar codes without guessing enums, scaling, units or sentinels."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    result = str(value).strip()
    if not result or result.lower() in ("null", "none", "nan", "inf", "-inf", "infinity", "-infinity"):
        return None
    if len(result) > 255 or any(ord(char) < 32 for char in result):
        return None
    return result
