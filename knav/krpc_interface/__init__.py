"""KRPC abstraction layer — sole point of contact between KNAV and KSP."""

from knav.krpc_interface.connection import KRPCConnection
from knav.krpc_interface.errors import (
    ConnectionLostError,
    KRPCError,
    ManeuverError,
    SceneNotSupportedError,
    StreamError,
    VesselNotAvailableError,
)
from knav.krpc_interface.scene import SceneManager
from knav.krpc_interface.streams import StreamManager

__all__ = [
    "ConnectionLostError",
    "KRPCConnection",
    "KRPCError",
    "ManeuverError",
    "SceneManager",
    "SceneNotSupportedError",
    "StreamError",
    "StreamManager",
    "VesselNotAvailableError",
]
