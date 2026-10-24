# Pentek IntelliDrive for Home Assistant

> [!WARNING]
> **Tested hardware and safety limits:** Physical validation was performed only
> on the maintainers' local installation using a
> [Pentek PID50 IntelliDrive Variable Frequency Drive](https://rcworst.com/products/pentek-pid50-intellidrive-variable-frequency-drive)
> and a
> [Waveshare RS485 to WiFi/Ethernet Serial Server and Modbus MQTT Gateway](https://www.amazon.com/dp/B0B4K1WN58).
> These results do not guarantee compatibility or safe operation with another
> drive, firmware revision, gateway, wiring arrangement, pump system, or network.
> Verify every value and state against the physical controller before relying on
> the integration. Use qualified electrical and pump-system professionals,
> de-energize and lock out equipment before wiring, preserve all independent
> pressure, dry-run, motor, and electrical protections, back up controller
> settings, and test while physically present. Never use Home Assistant as a
> safety controller. This project is provided as-is, without warranty; you assume
> all risk and responsibility for installation and use. The project authors and
> maintainers are not responsible for equipment damage, property damage, injury,
> downtime, data loss, or other consequences arising from its use.

A local, read-only Home Assistant integration for the Pentek IntelliDrive PID50
variable-frequency pump controller through a Modbus TCP-to-RS-485 gateway.

The first release intentionally exposes monitoring only. It contains no Modbus
write commands, switches, numbers, or services that can change pump behavior.

## Features

- UI configuration; no YAML is required.
- 49 holding-register sensors and three derived binary sensors.
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

- [Pentek IntelliDrive PID50](https://rcworst.com/products/pentek-pid50-intellidrive-variable-frequency-drive)
- [Waveshare RS485 to WiFi/Ethernet Serial Server and Modbus MQTT Gateway](https://www.amazon.com/dp/B0B4K1WN58)
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

Home Assistant **2026.10.2 or newer** is required. HACS custom-repository
installation is supported; inclusion in the default HACS catalog is separate.

## Migrating from Home Assistant Modbus YAML

Do not leave the old PID50 Modbus YAML polling the same gateway while this
integration is active. Some serial gateways can deliver a response to the wrong
TCP client when two clients poll concurrently.

Follow [MIGRATION.md](MIGRATION.md) for the backup, single-poller cutover,
entity mapping, enum-state changes, helper/history preservation, and rollback
checklist. Migration is manual: old entity IDs, raw sensor history, and
statistics are not automatically transferred.

## Polling behavior

Live values are polled every 15 seconds by default. Static configuration values
are refreshed every 30 minutes. The live interval can be changed from 5 to 300
seconds in the integration options.

A 100 ms pause is placed between Modbus blocks. Avoid aggressive intervals if
the gateway is also serving another diagnostic client.

## Entity availability

There are 52 native entities: 49 sensors and three binary sensors. Of these,
17 are enabled by default and 35 diagnostic sensors are disabled by default.
Enable individual diagnostics from the device page when needed, particularly
when migrating an existing dashboard.

Enum sensors expose named states such as `sleeping` and `fault_recovery`, plus
the numeric source in a `raw_value` attribute. A nonzero fault code can be
historical; use **Fault active** to detect an active fault or fault recovery.

An [example dashboard](examples/dashboard.yaml) is included. Its entity IDs are
placeholders; replace them with the IDs created in your installation.

## Safety

This project is not affiliated with Pentair or Pentek. It is community software,
not a safety controller. Home Assistant must never be the only protection for
over-pressure, dry-run, electrical, or motor faults.

Versions 0.1.x are read-only. Future write support, if added, must be explicitly
enabled and must include range validation, confirmation, read-back verification,
and clear documentation of controller-specific risks.

## Release status

Version 0.1.0 is an initial, read-only release. Automated protocol, packaging,
migration, and Home Assistant lifecycle tests cover the supported behavior.

Post-release hardware validation on the reference PID50 installation was
completed on October 23, 2026. Controller-display comparisons passed during
idle/sleeping and normal running operation, natural operating transitions were
observed, a 48-hour recorder window was reviewed, and a gateway-loss test marked
all entities unavailable before they recovered automatically without restarting
Home Assistant. The physical controller continued operating normally.

This does not validate every register, controller revision, or intentionally
induced fault condition. No controller settings are written. See
[AUDIT.md](AUDIT.md) for the evidence and remaining validation limits, and the
[v0.1.0 release notes](docs/releases/v0.1.0.md) for the release scope.

## License

MIT
