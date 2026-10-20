"""Verified PID50 register definitions and decoding helpers."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from math import isfinite
from typing import Final, Literal

RegisterKind = Literal["uint16", "uint32", "float32"]
PollClass = Literal["fast", "slow"]


@dataclass(frozen=True, kw_only=True)
class RegisterDefinition:
    """Describe one exposed holding-register value."""

    key: str
    name: str
    address: int
    kind: RegisterKind = "uint16"
    poll: PollClass = "slow"
    scale: float = 1.0
    precision: int | None = None
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    icon: str | None = None
    enum_map: dict[int, str] | None = None
    enabled_default: bool = False

    @property
    def words(self) -> int:
        """Return the Modbus word count used by the value."""
        return 2 if self.kind in ("uint32", "float32") else 1


@dataclass(frozen=True, kw_only=True)
class RegisterBlock:
    """A bounded contiguous Modbus read."""

    address: int
    count: int


OPERATION_STATES: Final = {
    0: "stopped",
    1: "initializing",
    2: "target_pressure",
    3: "boosting",
    4: "sleeping",
    5: "maintaining",
    6: "stopping",
    7: "fault",
    8: "fault_recovery",
}
RUN_MODES: Final = {0: "stop", 1: "pump_out", 2: "auto"}
MOTOR_TYPES: Final = {
    0: "three_phase",
    1: "single_phase_two_wire",
    2: "single_phase_three_wire",
}
INPUT_FUNCTIONS: Final = {
    0: "unused",
    1: "run_enable",
    2: "external_fault",
    3: "external_setpoint",
}
OUTPUT_FUNCTIONS: Final = {0: "unused", 1: "running", 2: "fault"}
PRESSURE_UNITS: Final = {0: "psi", 1: "kpa"}
BOOLEAN_VALUES: Final = {0: "disabled", 1: "enabled"}


REGISTERS: Final[tuple[RegisterDefinition, ...]] = (
    RegisterDefinition(
        key="pressure",
        name="Pressure",
        address=221,
        poll="fast",
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="pressure_setpoint",
        name="Pressure setpoint",
        address=218,
        poll="fast",
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="transducer_max",
        name="Transducer maximum",
        address=220,
        scale=0.14504,
        precision=0,
        unit="psi",
        device_class="pressure",
        state_class="measurement",
    ),
    RegisterDefinition(
        key="setpoint_external",
        name="External setpoint",
        address=229,
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
        state_class="measurement",
    ),
    RegisterDefinition(
        key="setpoint_overpressure",
        name="Overpressure setpoint",
        address=257,
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
        state_class="measurement",
    ),
    RegisterDefinition(
        key="operation_state",
        name="Operation state",
        address=40,
        poll="fast",
        enum_map=OPERATION_STATES,
        enabled_default=True,
    ),
    RegisterDefinition(
        key="run_mode",
        name="Run mode",
        address=41,
        poll="fast",
        enum_map=RUN_MODES,
        enabled_default=True,
    ),
    RegisterDefinition(
        key="fault_code",
        name="Fault code",
        address=30,
        kind="uint32",
        poll="fast",
        icon="mdi:alert-circle-outline",
        enabled_default=True,
    ),
    RegisterDefinition(key="p_gain", name="P gain", address=208),
    RegisterDefinition(key="t_integral", name="Integral time", address=209, unit="ms"),
    RegisterDefinition(
        key="t_derivative", name="Derivative time", address=210, unit="ms"
    ),
    RegisterDefinition(key="derivative_limit", name="Derivative limit", address=211),
    RegisterDefinition(
        key="frequency_max",
        name="Maximum frequency",
        address=233,
        unit="Hz",
        device_class="frequency",
    ),
    RegisterDefinition(
        key="frequency_min",
        name="Minimum frequency",
        address=234,
        unit="Hz",
        device_class="frequency",
    ),
    RegisterDefinition(
        key="pumpout_speed",
        name="Pump-out speed",
        address=213,
        unit="Hz",
        device_class="frequency",
    ),
    RegisterDefinition(
        key="io_input_1_active",
        name="Input 1 active",
        address=203,
        poll="fast",
        enum_map=BOOLEAN_VALUES,
    ),
    RegisterDefinition(
        key="io_input_2_active",
        name="Input 2 active",
        address=204,
        poll="fast",
        enum_map=BOOLEAN_VALUES,
    ),
    RegisterDefinition(
        key="io_output_active",
        name="Output active",
        address=205,
        poll="fast",
        enum_map=BOOLEAN_VALUES,
    ),
    RegisterDefinition(
        key="io_input_1_function",
        name="Input 1 function",
        address=230,
        enum_map=INPUT_FUNCTIONS,
    ),
    RegisterDefinition(
        key="io_input_2_function",
        name="Input 2 function",
        address=231,
        enum_map=INPUT_FUNCTIONS,
    ),
    RegisterDefinition(
        key="io_output_function",
        name="Output function",
        address=254,
        enum_map=OUTPUT_FUNCTIONS,
    ),
    RegisterDefinition(
        key="dry_run_detection_time",
        name="Dry-run detection time",
        address=223,
        unit="s",
    ),
    RegisterDefinition(
        key="dry_run_reset_limit", name="Dry-run reset limit", address=224
    ),
    RegisterDefinition(
        key="dry_run_reset_delay", name="Dry-run reset delay", address=225, unit="min"
    ),
    RegisterDefinition(
        key="dry_run_fill_time", name="Dry-run fill time", address=228, unit="s"
    ),
    RegisterDefinition(
        key="dry_run_sensitivity",
        name="Dry-run sensitivity",
        address=258,
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
    ),
    RegisterDefinition(
        key="sleep_wakeup_diff",
        name="Sleep wake-up differential",
        address=249,
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
    ),
    RegisterDefinition(
        key="sleep_wakeup_delay", name="Sleep wake-up delay", address=250, unit="s"
    ),
    RegisterDefinition(
        key="sleep_boost_delay", name="Sleep boost delay", address=251, unit="s"
    ),
    RegisterDefinition(
        key="sleep_boost_diff",
        name="Sleep boost differential",
        address=252,
        scale=0.14504,
        precision=1,
        unit="psi",
        device_class="pressure",
    ),
    RegisterDefinition(
        key="pipe_break_enabled",
        name="Pipe-break protection",
        address=240,
        enum_map=BOOLEAN_VALUES,
    ),
    RegisterDefinition(
        key="pipe_break_hours", name="Pipe-break hours", address=239, unit="h"
    ),
    RegisterDefinition(
        key="pressure_unit", name="Pressure unit", address=217, enum_map=PRESSURE_UNITS
    ),
    RegisterDefinition(
        key="frequency",
        name="Frequency",
        address=5145,
        kind="float32",
        poll="fast",
        precision=1,
        unit="Hz",
        device_class="frequency",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="actual_speed",
        name="Actual speed",
        address=5142,
        kind="float32",
        poll="fast",
        precision=1,
        icon="mdi:speedometer",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="power",
        name="Power",
        address=5149,
        kind="uint32",
        poll="fast",
        unit="W",
        device_class="power",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="phase_a_current",
        name="Phase A current",
        address=5151,
        kind="float32",
        poll="fast",
        precision=2,
        unit="A",
        device_class="current",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="phase_b_current",
        name="Phase B current",
        address=5153,
        kind="float32",
        poll="fast",
        precision=2,
        unit="A",
        device_class="current",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="phase_c_current",
        name="Phase C current",
        address=5155,
        kind="float32",
        poll="fast",
        precision=2,
        unit="A",
        device_class="current",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="phase_voltage",
        name="Phase voltage",
        address=5157,
        kind="float32",
        poll="fast",
        precision=1,
        unit="V",
        device_class="voltage",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="supply_voltage",
        name="Supply voltage",
        address=5203,
        kind="uint32",
        poll="fast",
        unit="V",
        device_class="voltage",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="igbt_temperature",
        name="IGBT temperature",
        address=5205,
        kind="float32",
        poll="fast",
        precision=1,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        enabled_default=True,
    ),
    RegisterDefinition(
        key="motor_sf_amps",
        name="Motor service-factor amps",
        address=5200,
        kind="float32",
        precision=1,
        unit="A",
        device_class="current",
    ),
    RegisterDefinition(
        key="motor_type", name="Motor type", address=5202, enum_map=MOTOR_TYPES
    ),
    RegisterDefinition(
        key="motor_above_ground",
        name="Motor location",
        address=5499,
        enum_map={0: "submersible", 1: "above_ground"},
    ),
    RegisterDefinition(
        key="ramp_up_time", name="Ramp-up time", address=5500, unit="ms"
    ),
    RegisterDefinition(
        key="ramp_down_time", name="Ramp-down time", address=5501, unit="ms"
    ),
    RegisterDefinition(
        key="ground_fault_limit",
        name="Ground-fault limit",
        address=5314,
        scale=0.1,
        precision=1,
        unit="A",
        device_class="current",
    ),
    RegisterDefinition(key="unit_number", name="Unit number", address=5022),
)

REGISTER_BY_KEY: Final = {register.key: register for register in REGISTERS}

# The PID50/serial gateway was validated with bounded reads of eight words or fewer.
FAST_BLOCKS: Final = (
    RegisterBlock(address=30, count=2),
    RegisterBlock(address=40, count=2),
    RegisterBlock(address=203, count=3),
    RegisterBlock(address=218, count=4),
    RegisterBlock(address=5142, count=6),
    RegisterBlock(address=5149, count=8),
    RegisterBlock(address=5157, count=2),
    RegisterBlock(address=5203, count=4),
)

SLOW_BLOCKS: Final = (
    RegisterBlock(address=208, count=6),
    RegisterBlock(address=217, count=8),
    RegisterBlock(address=225, count=5),
    RegisterBlock(address=230, count=5),
    RegisterBlock(address=239, count=2),
    RegisterBlock(address=249, count=4),
    RegisterBlock(address=254, count=1),
    RegisterBlock(address=257, count=2),
    RegisterBlock(address=5022, count=1),
    RegisterBlock(address=5200, count=3),
    RegisterBlock(address=5314, count=1),
    RegisterBlock(address=5499, count=3),
)


def decode_register(register: RegisterDefinition, words: dict[int, int]) -> int | float:
    """Decode one definition from an address-to-word mapping."""
    raw_words = [words[register.address + offset] for offset in range(register.words)]
    if register.kind == "uint16":
        value: int | float = raw_words[0]
    elif register.kind == "uint32":
        value = (raw_words[0] << 16) | raw_words[1]
    else:
        value = struct.unpack(">f", struct.pack(">HH", *raw_words))[0]

    if register.scale != 1.0:
        value *= register.scale
    if isinstance(value, float) and not isfinite(value):
        msg = f"register {register.address} decoded to a non-finite value"
        raise ValueError(msg)
    if register.precision is not None:
        value = round(value, register.precision)
    return value


def decode_registers(words: dict[int, int]) -> dict[str, int | float]:
    """Decode every definition whose complete word range is present."""
    result: dict[str, int | float] = {}
    for register in REGISTERS:
        if all(register.address + offset in words for offset in range(register.words)):
            try:
                result[register.key] = decode_register(register, words)
            except ValueError:
                continue
    return result
