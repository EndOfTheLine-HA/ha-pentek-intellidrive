"""Tests for strict Modbus TCP response handling."""

from __future__ import annotations

import struct

import pytest

from custom_components.pentek_intellidrive.api import (
    PentekConnectionError,
    PentekModbusClient,
)


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
