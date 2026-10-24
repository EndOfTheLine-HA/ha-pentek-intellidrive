"""Tests for strict Modbus TCP response handling."""

from __future__ import annotations

import struct

import pytest

from custom_components.pentek_intellidrive.api import (
    PentekConnectionError,
    PentekModbusClient,
)
from custom_components.pentek_intellidrive.registers import FAST_BLOCKS, SLOW_BLOCKS


class FakeSocket:
    """Minimal context-managed socket that echoes a generated Modbus reply."""

    def __init__(self, *, foreign_transaction: bool = False) -> None:
        self.foreign_transaction = foreign_transaction
        self.response = bytearray()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def sendall(self, frame: bytes) -> None:
        transaction_id, _, _, unit_id = struct.unpack(">HHHB", frame[:7])
        if self.foreign_transaction:
            transaction_id = transaction_id % 65535 + 1
        body = bytes((3, 4)) + struct.pack(">HH", 10, 20)
        header = struct.pack(">HHHB", transaction_id, 0, len(body) + 1, unit_id)
        self.response = bytearray(header + body)

    def recv(self, count: int) -> bytes:
        chunk = bytes(self.response[:count])
        del self.response[:count]
        return chunk


def _client() -> PentekModbusClient:
    return PentekModbusClient("example.local", 502, 2, 1, 0, retries=1)


def test_valid_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeSocket()
    monkeypatch.setattr("socket.create_connection", lambda *args, **kwargs: fake)
    assert _client().read_holding_registers(100, 2) == [10, 20]


def test_foreign_transaction_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeSocket(foreign_transaction=True)
    monkeypatch.setattr("socket.create_connection", lambda *args, **kwargs: fake)
    with pytest.raises(PentekConnectionError):
        _client().read_holding_registers(100, 2)


class DripSocket(FakeSocket):
    """Answers one byte per recv, each taking 0.4 s on a fake clock."""

    def __init__(self, clock: list[float]) -> None:
        super().__init__()
        self.clock = clock
        self.delivered = 0

    def recv(self, count: int) -> bytes:
        self.clock[0] += 0.4
        self.delivered += 1
        return super().recv(1)


def test_slow_drip_gateway_hits_one_overall_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [1000.0]
    fake = DripSocket(clock)
    monkeypatch.setattr("socket.create_connection", lambda *args, **kwargs: fake)
    monkeypatch.setattr(
        "custom_components.pentek_intellidrive.api.time.monotonic", lambda: clock[0]
    )
    with pytest.raises(PentekConnectionError) as err:
        _client().read_holding_registers(100, 2)  # 1 s timeout
    assert "timed out" in str(err.value.__cause__)
    # Every byte arrived well inside a per-recv timeout, yet the read stopped
    # at the 1 s budget instead of waiting for the full 13-byte reply.
    assert fake.delivered <= 3


class SendTimingSocket(FakeSocket):
    """Records the socket timeout in force when the request is sent."""

    def sendall(self, frame: bytes) -> None:
        self.timeout_at_send = self.timeout
        super().sendall(frame)


def _slow_connect(monkeypatch, fake, clock, seconds):
    def connect(*args, **kwargs):
        clock[0] += seconds  # the TCP handshake used part of the budget
        return fake

    monkeypatch.setattr("socket.create_connection", connect)
    monkeypatch.setattr(
        "custom_components.pentek_intellidrive.api.time.monotonic", lambda: clock[0]
    )


def test_send_gets_only_the_time_left_after_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [1000.0]
    fake = SendTimingSocket()
    _slow_connect(monkeypatch, fake, clock, 0.75)
    assert _client().read_holding_registers(100, 2) == [10, 20]  # 1 s timeout
    assert fake.timeout_at_send == pytest.approx(0.25)


def test_connect_that_uses_the_whole_budget_sends_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [1000.0]
    fake = SendTimingSocket()
    _slow_connect(monkeypatch, fake, clock, 1.5)
    with pytest.raises(PentekConnectionError) as err:
        _client().read_holding_registers(100, 2)
    assert "timed out" in str(err.value.__cause__)
    assert not hasattr(fake, "timeout_at_send")


class BadLengthSocket(FakeSocket):
    """Announces a 5,000-byte body in an otherwise valid header."""

    def sendall(self, frame: bytes) -> None:
        transaction_id, _, _, unit_id = struct.unpack(">HHHB", frame[:7])
        self.response = bytearray(
            struct.pack(">HHHB", transaction_id, 0, 5000, unit_id)
        )
        self.requested: list[int] = []

    def recv(self, count: int) -> bytes:
        self.requested.append(count)
        return super().recv(count)


def test_invalid_length_is_rejected_before_reading_the_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = BadLengthSocket()
    monkeypatch.setattr("socket.create_connection", lambda *args, **kwargs: fake)
    with pytest.raises(PentekConnectionError) as err:
        _client().read_holding_registers(100, 2)
    assert "reply length" in str(err.value.__cause__)
    assert max(fake.requested) <= 7  # Only the header was ever asked for.


class RecordingSocket(FakeSocket):
    """Records every request and answers with zeroed registers of the right size."""

    frames: list[bytes] = []

    def sendall(self, frame: bytes) -> None:
        RecordingSocket.frames.append(frame)
        transaction_id, _, _, unit_id = struct.unpack(">HHHB", frame[:7])
        count = struct.unpack(">H", frame[10:12])[0]
        body = bytes((3, count * 2)) + b"\x00\x00" * count
        header = struct.pack(">HHHB", transaction_id, 0, len(body) + 1, unit_id)
        self.response = bytearray(header + body)


def test_every_request_is_a_function_code_3_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RecordingSocket.frames = []
    monkeypatch.setattr(
        "socket.create_connection", lambda *args, **kwargs: RecordingSocket()
    )
    _client().read_blocks((*FAST_BLOCKS, *SLOW_BLOCKS))
    assert len(RecordingSocket.frames) == len(FAST_BLOCKS) + len(SLOW_BLOCKS)
    for frame in RecordingSocket.frames:
        # MBAP header (7 bytes) + function code + address + count: a read.
        assert len(frame) == 12 and frame[7] == 3
