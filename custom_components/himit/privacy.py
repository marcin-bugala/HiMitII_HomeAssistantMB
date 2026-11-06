"""Redact identifiers and credentials from exported diagnostics."""
from __future__ import annotations

from typing import Any

_PRIVATE_KEYS = {
    "username", "password", "email", "accesstoken", "refreshtoken", "token",
    "authorization", "homeid", "homename", "bindid", "wifiid", "wifimac",
    "mac", "macaddress", "ip", "ipaddress", "ssid", "customerid", "userid",
    "deviceid", "devicenickname", "devicename", "name", "floorid", "floorname",
    "roomid", "roomname", "serial", "serialnumber", "sn", "address",
    "longitude", "latitude", "phone", "phonenumber", "verificationcode",
}


def redact_diagnostics(value: Any) -> Any:
    """Copy nested JSON, including internal underscored keys, without mutating it."""
    if isinstance(value, dict):
        return {
            key: "**REDACTED**"
            if str(key).replace("_", "").lower() in _PRIVATE_KEYS
            else redact_diagnostics(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_diagnostics(item) for item in value]
    return value
