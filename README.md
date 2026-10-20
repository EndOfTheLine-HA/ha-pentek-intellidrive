# Pentek IntelliDrive for Home Assistant

A local, read-only Home Assistant integration for the Pentek IntelliDrive PID50
variable-frequency pump controller through a Modbus TCP-to-RS-485 gateway.

The first release intentionally exposes monitoring only. It contains no Modbus
write commands, switches, numbers, or services that can change pump behavior.

## Features

- UI configuration; no YAML is required.
- 49 verified holding-register sensors.
- Live pressure, setpoint, frequency, power, current, voltage, temperature,
  operating state, run mode, and fault code.
- Diagnostic views of PID tuning, dry-run protection, sleep/boost behavior,
  pipe-break settings, I/O functions, and motor configuration.
- Derived `Running`, `Sleeping`, and `Fault active` binary sensors.
- Strict validation of Modbus transaction ID, unit ID, function code, payload
  length, and exception responses.
- Bounded reads of no more than eight 16-bit words and serialized requests for
  gateways that do not tolerate concurrent clients well.

## Hardware and protocol

This integration has been developed against:

- Pentek IntelliDrive PID50
- a Modbus TCP-to-RS-485 gateway
- Modbus unit ID `2`
- TCP port `502`
- big-endian holding registers (function code 3)

Other IntelliDrive models or register-map revisions are not yet confirmed.

## Install with HACS

1. Open HACS.
2. Add `https://github.com/EndOfTheLine-HA/ha-pentek-intellidrive` as a custom
   integration repository.
3. Install **Pentek IntelliDrive**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration** and search for
   **Pentek IntelliDrive**.
6. Enter the gateway host, port, unit ID, and polling interval.

## Migrating from Home Assistant Modbus YAML

Do not leave the old PID50 Modbus YAML polling the same gateway while this
integration is active. Some serial gateways can deliver a response to the wrong
TCP client when two clients poll concurrently.

Recommended migration:

1. Back up the current Home Assistant configuration and entity customizations.
2. Record the entity IDs used by dashboards, automations, statistics, and energy
   sensors.
3. Disable the old PID50 Modbus YAML and restart Home Assistant.
4. Add this integration and confirm its readings against the drive display.
5. Rename the new entities or update consumers deliberately.
6. Keep the old YAML backup until the new entities have been physically
   validated through stopped, running, sleeping, and fault-free operation.

The integration does not automatically migrate YAML-created entity registry
entries.

## Polling behavior

Live values are polled every 15 seconds by default. Static configuration values
are refreshed every 30 minutes. The live interval can be changed from 5 to 300
seconds in the integration options.

A 100 ms pause is placed between Modbus blocks. Avoid aggressive intervals if
the gateway is also serving another diagnostic client.

## Entity availability

Frequently changing entities are enabled by default. Slow-changing settings are
created as diagnostic entities and disabled by default; enable them from the
device page when needed. All 49 register definitions remain available.

## Safety

This project is not affiliated with Pentair or Pentek. It is community software,
not a safety controller. Home Assistant must never be the only protection for
over-pressure, dry-run, electrical, or motor faults.

Version 0.1.0 is read-only. Future write support, if added, must be explicitly
enabled and must include range validation, confirmation, read-back verification,
and clear documentation of controller-specific risks.

## Development status

- Register map: derived from a working 49-entity Home Assistant installation and
  direct read tools.
- Automated validation: protocol decoding, package structure, Ruff, HACS, and
  Hassfest workflows are included.
- Physical validation of the packaged custom integration: still required before
  a production migration.

See [AUDIT.md](AUDIT.md) for provenance and validation boundaries.

## License

MIT
