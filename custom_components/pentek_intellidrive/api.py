"""Small, strict Modbus TCP reader for the Pentek IntelliDrive."""

from __future__ import annotations

import secrets
import socket
import struct
import time
from collections.abc import Iterable

from .registers import RegisterBlock


class PentekConnectionError(Exception):
    """Raised when the gateway response is missing or invalid."""


class PentekModbusClient:
    """Read-only Modbus TCP client with strict reply validation."""

    def __init__(
        self,
        host: str,
        port: int,
        unit_id: int,
        timeout: float,
        message_wait: float,
        retries: int = 3,
    ) -> None:
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.message_wait = message_wait
        self.retries = retries

    def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read holding registers using Modbus function code 3."""
        if not 1 <= count <= 125:
            raise ValueError("count must be between 1 and 125")

        last_error: Exception | None = None
        for attempt in range(self.retries):
            transaction_id = secrets.randbelow(65534) + 1
            pdu = struct.pack(">BHH", 3, address, count)
            frame = (
                struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, self.unit_id)
                + pdu
            )
            try:
                with socket.create_connection(
                    (self.host, self.port), timeout=self.timeout
                ) as sock:
                    sock.settimeout(self.timeout)
                    sock.sendall(frame)
                    header = self._recv_exact(sock, 7)
                    reply_id, protocol_id, length, unit_id = struct.unpack(
                        ">HHHB", header
                    )
                    body = self._recv_exact(sock, length - 1)

                if reply_id != transaction_id:
                    raise PentekConnectionError(
                        "gateway returned a foreign transaction"
                    )
                if protocol_id != 0 or unit_id != self.unit_id:
                    raise PentekConnectionError(
                        "gateway returned invalid Modbus metadata"
                    )
                if body and body[0] == 0x83:
                    code = body[1] if len(body) > 1 else "unknown"
                    raise PentekConnectionError(
                        f"device returned Modbus exception {code}"
                    )
                if len(body) != 2 + (count * 2) or body[0] != 3 or body[1] != count * 2:
                    raise PentekConnectionError(
                        "gateway returned an invalid register payload"
                    )

                return list(struct.unpack(f">{count}H", body[2:]))
            except (OSError, struct.error, PentekConnectionError) as err:
                last_error = err
                if attempt + 1 < self.retries:
                    time.sleep(0.4 * (attempt + 1))

        raise PentekConnectionError(
            f"unable to read holding registers at {address}"
        ) from last_error

    def read_blocks(self, blocks: Iterable[RegisterBlock]) -> dict[int, int]:
        """Read bounded blocks sequentially and return words keyed by address."""
        words: dict[int, int] = {}
        for block in blocks:
            values = self.read_holding_registers(block.address, block.count)
            words.update(
                {block.address + offset: value for offset, value in enumerate(values)}
            )
            if self.message_wait:
                time.sleep(self.message_wait)
        return words

    def test_connection(self) -> int:
        """Read the verified pressure register and return its raw value."""
        return self.read_holding_registers(221, 1)[0]

    @staticmethod
    def _recv_exact(sock: socket.socket, count: int) -> bytes:
        """Receive exactly count bytes or raise."""
        data = bytearray()
        while len(data) < count:
            chunk = sock.recv(count - len(data))
            if not chunk:
                raise PentekConnectionError("gateway closed the connection")
            data.extend(chunk)
        return bytes(data)
