# Hi-Mit II — Home Assistant Integration

A custom Home Assistant integration for the **Hisense Hi-Mit II Air-to-Water heat pump** (ATW), reverse-engineered from the official mobile app APK.

This fork is maintained at [marcin-bugala/HiMitII_HomeAssistantMB](https://github.com/marcin-bugala/HiMitII_HomeAssistantMB).
The original integration is by [danardelean](https://github.com/danardelean/HiMitII_HomeAssistant).
Automatic re-login and Polish translations are adapted from
[elektron81's upstream PR #1](https://github.com/danardelean/HiMitII_HomeAssistant/pull/1)
(head `6ffa48d5e1f6c8e733ea879eafcc91289b0f9181`).
The `himit` domain and existing unique IDs are preserved. Install this fork in
place of the original integration. Registered entity IDs are retained; names for
new entities follow the Home Assistant language. User-assigned names are retained.

---

## Features

### Read-only telemetry extension (1.2.0)

Adds 30 diagnostic entities using the existing coordinator snapshot, with no
additional API requests or new control actions. All **30 new diagnostic entities**
are enabled by default for recording and comparison. Updating this fork also enables
these additions if they were disabled by the integration's previous defaults.
Entities explicitly disabled by the user remain disabled.

- 14 experimental binary flags: space heating/DHW defrost, four frost protection
  flags, ECO, night, quiet, electric heating, disinfection, Anti Legionella,
  DHW boost and emergency mode.
- 16 raw sensors: alarm code, actual run mode, mode and 13 telemetry fields
  (`Twi`, `Two`, `Twohp`, `Pw`, `PWM`, `Fd`, `Q_p`, `Power_heating`,
  `Capacity_heating`, `Power_DHW`, `Capacity_DHW`, `EH1_Power`, `EH2_Power`).

Each addition exposes `source_field` and `mapping_confidence`. Enabled status does
not change the experimental confidence of the mappings. Field presence
was confirmed in a device snapshot, but event semantics, scaling and units have
not been verified. Experimental flags interpret only explicit 0/1 or true/false;
missing or invalid values make the entity unavailable. Raw sensors preserve codes
and zero values, without units, state classes or inferred labels. A zero could
be a placeholder. No COP, compressor-running inference or combined defrost signal
is calculated. Do not use experimental cloud flags as the sole protection signal.

Existing entity keys, unique IDs and controls are preserved. In particular,
**Heat Pump Running** still reads `A2W_SW_ON` for compatibility; this indicates
the main enable flag and does **not** establish that the compressor is running.
Existing switches and number entities remain writable as before.

Diagnostics now redact additional nested identifiers and replace device-state
dictionary keys with `device_1`, etc. Treat diagnostic files as private and check
them before sharing: unknown vendor fields may contain additional identifiers.

Offline tests use sanitized telemetry only. Run `python -m pytest -q` with
Home Assistant installed. These tests do not contact Hisense or control a pump.

### Authentication and translations from PR #1

Token updates do not reload the integration; changed options still do. Rejected
refresh tokens fall back to stored credentials. A rejected data-access token
(including HTTP 401/403) triggers one login and one read retry. Connection and
timeout failures report temporary unavailability. A second authentication rejection
requires reauthentication. This fork also fixes indentation and duplicated/unreachable
code introduced while copying the PR into the fork.

Polish and English entity translations cover all platforms and the 30 new
diagnostics. HACS metadata and documentation URLs point to this fork.

| Platform | Entity | Description |
|---|---|---|
| `binary_sensor` | Heat Pump Running | Reports whether the compressor / A2W unit is active |
| `sensor` | Circuit 1 Water Temp | Live actual water temperature — Circuit 1 (fixedDid18) |
| `sensor` | Circuit 2 Water Temp | Live actual water temperature — Circuit 2 (fixedDid19) |
| `sensor` | DHW Water Temp | Live actual domestic hot water temperature (fixedDid16) |
| `sensor` | Pool Water Temp | Live actual swimming pool temperature (fixedDid17) |
| `sensor` | Outdoor Ambient Temp | External sensor reading (swj_Ta) |
| `sensor` | Room 1–8 Temp | Individual room sensor readings (TsR1–TsR8) |
| `switch` | Circuit 1 (Heating) | Enable / disable Circuit 1 |
| `switch` | Circuit 2 (Heating) | Enable / disable Circuit 2 |
| `switch` | Domestic Hot Water | Enable / disable DHW heating |
| `switch` | Swimming Pool | Enable / disable pool heating |
| `number` | Circuit 1 Setpoint | Water temperature target for Circuit 1 (°C) |
| `number` | Circuit 2 Setpoint | Water temperature target for Circuit 2 (°C) |
| `number` | DHW Setpoint | Domestic hot water target temperature (°C) |
| `number` | Pool Setpoint | Pool water target temperature (°C) |

**Setpoint min/max limits are read live from the device** (the pump reports its own allowed ranges per heating/cooling mode).

Exception in this fork: Circuit 1 has a fixed minimum setpoint of **20°C**.

---

## Installation

### HACS (recommended)

1. In HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/marcin-bugala/HiMitII_HomeAssistantMB`, category **Integration**
3. Install **Hi-Mit II**
4. Restart Home Assistant

### Manual

```bash
# From your HA config directory
git clone https://github.com/marcin-bugala/HiMitII_HomeAssistantMB.git /tmp/himit
cp -r /tmp/himit/custom_components/himit config/custom_components/himit
```

Restart Home Assistant.

---

## Configuration

1. **Settings → Integrations → Add Integration**
2. Search for **Hi-Mit II**
3. Enter your Hisense / Hi-Mit II account email and password
4. If your account has multiple homes, select the one with your heat pump
5. Done — entities appear immediately and update every 30 seconds

### Token handling

The integration handles authentication automatically:

- The access token is **refreshed silently** before it expires using the stored refresh token
- If the refresh token also expires, a **Re-authenticate** prompt appears in the Integrations page — no need to delete and re-add the integration
- All tokens are stored securely in the Home Assistant config entry (`.storage/`)

---

## Forcing a Data Refresh

By default the integration polls every 30 seconds. If you need an immediate update there are two options:

### 1. Built-in service call (no code changes needed)

Call the standard Home Assistant service on any of the integration's entities:

```yaml
service: homeassistant.update_entity
target:
  entity_id: sensor.hi_mit_ii_circuit_1_water_temp
```

This triggers `coordinator.async_request_refresh()` immediately.

### 2. Dedicated Refresh button entity

A `button` platform can be added to expose a single **Refresh** button in the UI / dashboard:

```python
class HimitRefreshButton(HimitEntity, ButtonEntity):
    _attr_name = "Refresh"
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
```

Press it from a dashboard card or use it in an automation and data updates instantly.

---

## How it works

This integration was built by reverse-engineering the official **Hi-Mit II Android APK**:

- **RSA request signing** — every API request is signed using RSA-PKCS1v15 with a 2048-bit public key embedded in the APK (`assets/rsa_public_key.key`). The server holds the private key and decrypts to verify.
- **Password encoding** — the login password is MD5-hashed (uppercase), then RSA-encrypted with a separate 512-bit key (`assets/rsa_account_public_key.key`).
- **Temperature field mapping** — actual live temperatures come from `fixedDid16–19` fields (not obvious names), confirmed by tracing `doSetCycle1Item` / `doSetCycle2Item` in `HeatPumpControllActivity.java`:

  | Field | Description |
  |---|---|
  | `fixedDid18` | Circuit 1 actual water temp (tvTag333 in app UI) |
  | `fixedDid19` | Circuit 2 actual water temp (tvTag444 in app UI) |
  | `fixedDid16` | DHW actual water temp (tvTag111 in app UI) |
  | `fixedDid17` | Pool actual water temp (tvTag222 in app UI) |

- **Control** — `POST /himit-dshd/setDeviceProperty` with a `properties` array of `{cmdType, cmdValue}` pairs. The sign covers all scalar fields plus the JSON-stringified properties array.

### API endpoints

All on `https://hmt-eu-gateway.hijuconn.com`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/account/acc/login_pwd` | Login (auth-gateway) |
| POST | `/account/acc/refresh_token` | Refresh access token |
| GET | `/himit-lgs/get_home_list` | List homes |
| GET | `/himit-dms/get_customer_device_list_info` | List devices |
| POST | `/himit-dshd/getDeviceProperty` | Full device state |
| POST | `/himit-dshd/setDeviceProperty` | Send control commands |

---

## File structure

```
custom_components/himit/
├── __init__.py          # Integration setup / teardown
├── api.py               # Async HTTP client (all crypto + API calls)
├── binary_sensor.py     # Read-only status sensors (A2W running)
├── config_flow.py       # UI login flow + home selection
├── const.py             # All constants (keys, field names, endpoints)
├── coordinator.py       # DataUpdateCoordinator — polling + token refresh
├── entity.py            # Shared base entity class
├── manifest.json        # HA integration manifest
├── number.py            # Temperature setpoint controls
├── sensor.py            # Temperature sensors
├── switch.py            # On/off switches
└── translations/
    └── en.json          # Config flow UI strings
```

---

## Requirements

- Home Assistant 2024.1 or newer
- Python packages (installed automatically): `cryptography>=41.0.0`, `aiohttp>=3.9.0`
- A valid Hisense / Hi-Mit II cloud account

---

## Disclaimer

This integration is not affiliated with or endorsed by Hisense. It was built by analysing the official mobile app for personal use. Use at your own risk.
