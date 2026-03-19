from pydantic import BaseModel


class TelemetryChannel(BaseModel):
    orbit: dict = {}
    flight: dict = {}
    propulsion: dict = {}
    resources: dict = {}


class TelemetryFrame(BaseModel):
    timestamp: float
    met: float
    channels: TelemetryChannel


class GuidanceCommand(BaseModel):
    """Output of Guidance, consumed by Control."""

    target_pitch: float = 0.0
    target_heading: float = 0.0
    target_roll: float | None = None
    throttle_command: float = 0.0
    sas_mode: str | None = None
    use_autopilot: bool = False
    warp_to_ut: float | None = None
    staging_request: bool = False
    terminate: bool = False
