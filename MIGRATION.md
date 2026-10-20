# Migrating an existing PID50 installation

This integration does not automatically migrate Modbus YAML entities, dashboards,
automations, helpers, or recorder statistics. Adapt the steps below to your
installation and current Home Assistant version.

## 1. Back up and inventory

- Create a Home Assistant backup and retain the original PID50 Modbus YAML,
  templates, automations, dashboards, and helper settings privately.
- Record each old entity ID and its consumers. Include storage dashboards and
  UI-created helpers, not just YAML files.
- Record energy and runtime totals before changing sources. Note helper entity
  IDs, unique IDs where applicable, units, integration method, utility-meter
  cycles, and any installation-specific flow calibration.
- Keep a mapping of old IDs to new IDs. Do not publish your private configuration
  or backup as an example.

## 2. Switch to one poller

Do not run the legacy PID50 Modbus hub and this integration against the same
gateway concurrently. The custom integration serializes its own requests; it
cannot serialize a separate client's traffic.

1. Remove or disable only the PID50 hub in the legacy Modbus configuration. Keep
   unrelated Modbus devices intact. Disable the entire `modbus:` include only
   if it contains no other hubs you need.
2. Restart Home Assistant to apply that change before configuring this
   integration. Removing YAML from disk alone does not stop an already running
   poller. If the custom integration is already active, disable its config entry
   while performing this cutover.
3. Install this repository through HACS, restart as required, and add or re-enable
   **Pentek IntelliDrive** through **Settings → Devices & services**.
4. Enter your gateway host, port, and drive unit ID. Start with the default
   15-second polling interval. Stop other diagnostic readers during validation.
5. Confirm fresh readings and compare pressure, setpoint, frequency, and power
   with the controller display or your known-good reader. Do not run both HA
   pollers to perform that comparison.

These steps stop or start Home Assistant polling, not the physical pump.
The integration sends reads only; it does not change controller settings.

## 3. Map entities and enable required diagnostics

Open the integration's device page and record the actual entity IDs. IDs in
[examples/dashboard.yaml](examples/dashboard.yaml) are illustrative, not a
guaranteed naming scheme. IDs can depend on device naming and existing registry
entries.

The integration creates 49 sensors and three binary sensors. Seventeen native
entities are enabled by default; 35 diagnostic sensors are disabled by default.
Enable the diagnostics referenced by your existing dashboards or templates.
An entity being disabled is different from an enabled entity being unavailable.

Use this mapping checklist:

| Existing consumer | Update to |
| --- | --- |
| Pressure, setpoint, frequency, electrical telemetry | Matching native sensor |
| Running, sleeping, active-fault logic | Native binary sensor, or an existing helper that mirrors it |
| Numeric operation/run-mode comparisons | Named enum state, or the `raw_value` attribute |
| Integral/energy and power-statistics helpers | Native power sensor, retaining the existing helper identity |
| Daily/monthly energy and runtime meters | Existing cumulative helper wherever possible |
| Flow estimates and irrigation checks | New source IDs, retaining your own calibration and thresholds |

### Enum states and fault handling

Some legacy Modbus sensors exposed numeric states. Native enum sensors expose
named machine states, which may be displayed with translated labels in the UI:

- Operation state `4` becomes `sleeping`.
- Operation state `7` becomes `fault`.
- Operation state `8` becomes `fault_recovery`.
- Run mode `2` becomes `auto`.

For example, a state trigger that previously used `to: "8"` on the old operation
sensor must use `to: fault_recovery` on the new sensor. Review conditions as well
as triggers. Prefer the native **Fault active** binary sensor when both fault
and recovery states should count as a problem.

If an existing text template needs its original numeric mapping, use the enum
sensor's `raw_value` attribute. For example, after substituting your entity ID:

```jinja
{{ state_attr('sensor.example_pump_operation_state', 'raw_value') }}
```

Handle unavailable/unknown sources explicitly. A retained template binary sensor
should have an availability template using `has_value()` for its native source,
so a disconnected drive is not silently reported as healthy.

A nonzero fault-code register can be a latched historical value. It is not by
itself proof of an active fault; the native **Fault active** binary sensor follows
operation states 7 and 8. Do not intentionally cause a fault to test an alert.

## 4. Preserve helpers and understand history boundaries

- Update existing helpers in place through their supported UI/options flow, or
  YAML configuration where appropriate. Do not edit live `.storage` files.
- Retain existing integral/energy, statistics, utility-meter, and runtime helper
  identities instead of deleting and recreating them. Change only the necessary
  source references and preserve their other settings.
- Keep units consistent: native power is in watts. Verify the integral helper's
  conversion to the energy unit expected by your existing meters.
- Update dashboards, template sources, automation triggers and conditions,
  energy source references, and UI-created statistics/flow helpers. Do not copy
  another installation's flow calibration or safety thresholds.
- Reload supported components or restart Home Assistant for YAML changes that
  require it. Check restored helper totals against your recorded baseline.

Retaining a helper identity can preserve its existing history and totals, but
does not automatically transfer the old raw Modbus sensor's recorder history or
long-term statistics to a new native sensor. Old raw entities may remain
unavailable in the registry while their history remains under the old IDs.
Renaming a new entity is not a history-migration procedure.

## 5. Validate and retain a rollback path

- Validate the Home Assistant configuration before restarting.
- After restart, verify fresh native readings, required diagnostic entities,
  template availability, automation references, and restored energy/runtime
  totals. Review related startup logs.
- Search active YAML, storage dashboards through the supported dashboard editor,
  and UI helper settings for remaining references to retired raw entities.
- Observe normal operation over time and compare readings with the controller.
  The initial release did not physically validate every mode, fault scenario,
  register value, or gateway-loss recovery; see [AUDIT.md](AUDIT.md).
- Keep backups and old entity-history records until you are satisfied with the
  migration. Deleting old entities is not required to stop legacy polling.

To roll back, disable the custom integration first, restore the legacy PID50
configuration and consumer references, then restart Home Assistant. Confirm that
only the legacy hub is polling. Restoring configuration does not automatically
merge history recorded under different entity IDs during the trial.
