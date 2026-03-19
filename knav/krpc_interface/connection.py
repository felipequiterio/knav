"""Singleton KRPC connection manager."""

from __future__ import annotations

import time

import krpc
import structlog

from knav.config import Settings
from knav.krpc_interface.errors import ConnectionLostError, VesselNotAvailableError

log = structlog.get_logger()


class KRPCConnection:
    """Manages the lifecycle of a single KRPC connection.

    Use ``KRPCConnection.get()`` to obtain the singleton instance.
    """

    _instance: KRPCConnection | None = None

    def __init__(self) -> None:
        self._conn: krpc.Client | None = None
        self._settings = Settings()

    # -- Singleton access --

    @classmethod
    def get(cls) -> KRPCConnection:
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Discard the singleton (useful for tests)."""
        if cls._instance is not None:
            cls._instance.disconnect()
            cls._instance = None

    # -- Properties --

    @property
    def conn(self) -> krpc.Client:
        if self._conn is None:
            raise ConnectionLostError("Not connected to KRPC")
        return self._conn

    @property
    def space_center(self):
        return self.conn.space_center

    @property
    def vessel(self):
        try:
            return self.space_center.active_vessel
        except krpc.error.RPCError as exc:
            raise VesselNotAvailableError("No active vessel available", original=exc) from exc

    @property
    def ut(self) -> float:
        return self.space_center.ut

    @property
    def is_connected(self) -> bool:
        return self._conn is not None and self.health_check()

    # -- Lifecycle --

    def connect(self) -> None:
        """Establish a new KRPC connection."""
        s = self._settings
        log.info(
            "krpc.connecting",
            address=s.krpc_address,
            rpc_port=s.krpc_rpc_port,
            stream_port=s.krpc_stream_port,
        )
        self._conn = krpc.connect(
            name=s.krpc_name,
            address=s.krpc_address,
            rpc_port=s.krpc_rpc_port,
            stream_port=s.krpc_stream_port,
        )
        log.info("krpc.connected")

    def disconnect(self) -> None:
        """Close the KRPC connection if open."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                log.warning("krpc.disconnect_error", exc_info=True)
            finally:
                self._conn = None
                log.info("krpc.disconnected")

    def reconnect(self) -> None:
        """Disconnect then reconnect with exponential backoff (1 s -> 30 s cap)."""
        self.disconnect()
        wait = 1.0
        cap = float(self._settings.krpc_reconnect_max_wait)
        while True:
            try:
                self.connect()
                return
            except Exception:
                log.warning("krpc.reconnect_failed", retry_in=wait)
                time.sleep(wait)
                wait = min(wait * 2, cap)

    def health_check(self) -> bool:
        """Return True if the connection is alive."""
        try:
            self._conn.krpc.get_status()  # type: ignore[union-attr]
            return True
        except Exception:
            return False
