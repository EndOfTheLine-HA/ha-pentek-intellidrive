# Source, privacy, and safety audit

## Privacy boundary

Private configuration was reviewed only to confirm protocol behavior and migration
requirements. This repository intentionally excludes personal names, private
addresses, credentials, phone targets, entity-registry identifiers, dashboard
content, device serial numbers, motor-specific limits, and configuration backups.

## Confirmed implementation behavior

- The integration performs read-only Modbus TCP holding-register queries through a
  user-configured gateway and unit ID.
- Function code 3 reads the PID50 register map.
- Pressure values use a `0.14504` conversion to PSI.
- 32-bit integer and IEEE-754 float values use big-endian word order.
- The register map includes pressure, frequency, electrical telemetry, operating
  state, run mode, fault code, and I/O state.
- A stored nonzero fault code may be historical; `Fault active` follows the
  operating-state values associated with an active fault.
- Requests are serialized, bounded, and checked for transaction ID, unit ID,
  function code, payload length, and finite decoded values.

## Deliberate exclusions

- No holding-register writes.
- No number, select, switch, button, or service entities.
- No automatic migration of YAML entities or recorder statistics.
- No assumption that other IntelliDrive models share the PID50 register map.
- No private dashboards, addresses, equipment identifiers, or calibration values.

## Validation boundary

Automated tests cover register decoding, bounded reads, invalid and non-finite
responses, read-only package surfaces, translations, migration guidance, and
Home Assistant lifecycle behavior. CI also runs Ruff, HACS validation, and
Hassfest.

Not every register or operating transition has been independently checked against
every controller revision. Real fault, fault-recovery, over-pressure, dry-run,
extended-soak, and gateway-loss scenarios are not claimed as validated. Other
drive models, firmware revisions, and gateways remain unverified.

This is community monitoring software, not a safety system. Keep the drive's
independent physical and electrical protections in service, and never induce a
pump fault merely to test this integration.
