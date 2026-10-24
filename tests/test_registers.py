"""Tests for the verified PID50 register map."""

from __future__ import annotations

import struct

from custom_components.pentek_intellidrive.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
)
from custom_components.pentek_intellidrive.registers import (
    FAST_BLOCKS,
    REGISTERS,
    SLOW_BLOCKS,
    decode_registers,
    merge_registers,
)


def _float_words(value: float) -> tuple[int, int]:
    return struct.unpack(">HH", struct.pack(">f", value))


def test_register_count_and_read_bounds() -> None:
    assert len(REGISTERS) == 49
    assert len({register.key for register in REGISTERS}) == 49
    assert max(block.count for block in (*FAST_BLOCKS, *SLOW_BLOCKS)) <= 8
    for register in REGISTERS:
        blocks = FAST_BLOCKS if register.poll == "fast" else SLOW_BLOCKS
        covered = {
            block.address + offset for block in blocks for offset in range(block.count)
        }
        assert all(
            register.address + offset in covered for offset in range(register.words)
        )


def test_decode_verified_value_types() -> None:
    frequency_words = _float_words(57.25)
    words = {
        221: 414,
        5145: frequency_words[0],
        5146: frequency_words[1],
        5149: 0x0001,
        5150: 0x0002,
    }
    data = decode_registers(words)
    assert data["pressure"] == 60.0
    assert data["frequency"] == 57.2
    assert data["power"] == 65538


def test_partial_values_are_not_decoded() -> None:
    data = decode_registers({5145: 0x4264})
    assert "frequency" not in data


def test_non_finite_float_is_not_exposed() -> None:
    data = decode_registers({5145: 0x7FC0, 5146: 0x0000})
    assert "frequency" not in data


def test_undecodable_value_is_dropped_not_left_stale() -> None:
    previous = {"frequency": 57.2, "pressure": 50.0, "unit_number": 2}
    words = {221: 414, 5145: 0x7FC0, 5146: 0x0000}  # pressure ok, frequency NaN
    data = merge_registers(previous, words)
    assert data["pressure"] == 60.0
    assert "frequency" not in data  # read this cycle but invalid: unavailable
    assert data["unit_number"] == 2  # not read this cycle: kept


def test_latched_fault_code_does_not_mean_active_fault() -> None:
    description = next(
        item for item in BINARY_SENSOR_DESCRIPTIONS if item.key == "fault_active"
    )
    assert not description.value_fn({"operation_state": 5, "fault_code": 1})
    assert description.value_fn({"operation_state": 7, "fault_code": 0})
