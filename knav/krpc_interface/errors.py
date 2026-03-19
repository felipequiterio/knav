"""Custom exception hierarchy for KRPC integration."""


class KRPCError(Exception):
    """Base exception for all KRPC-related errors."""

    def __init__(self, message: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original


class ConnectionLostError(KRPCError):
    """KRPC connection dropped unexpectedly."""


class VesselNotAvailableError(KRPCError):
    """No active vessel in the current scene."""


class SceneNotSupportedError(KRPCError):
    """Current game scene does not support the requested capability."""


class StreamError(KRPCError):
    """Error creating, reading, or managing a KRPC stream."""


class ManeuverError(KRPCError):
    """Error creating or executing a maneuver node."""
