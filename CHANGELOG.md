# Changelog

## 1.3.0 — 2026-11-10

- Prioritize four observed periodic candidates: Power_heating, Capacity_heating,
  Power_DHW and Capacity_DHW. They are enabled by default as ordinary sensors,
  still exposing raw values with no engineering units or statistics classes.
- Keep the other 26 additions as optional, unverified diagnostics. Their new-install
  defaults are disabled. Existing enabled entities and manual disables are preserved.
- Restrict the earlier auto-enable migration to the four periodic candidates.
- Add interpretation/validation attributes without changing source fields or IDs.
- Rename the displayed A2W enable flag to “Heat pump enabled” and remove the
  misleading RUNNING device class; keep a2w_running and its boolean states.
- Mark eight constant room readings as unverified diagnostics, disabled by default
  on new installs, retaining their IDs, values, units and statistics compatibility.
- Preserve CO1's fixed 20°C minimum, authentication recovery and all controls.
- No new endpoints, commands, inferred compressor state, kW/kWh conversions or COP.
