"""Event type definitions for the in-process pub/sub bus."""

from dataclasses import dataclass, field
from typing import Any

from knav.models.enums import AlertSeverity, EventType


@dataclass(frozen=True)
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


def telemetry_frame(channels: dict, timestamp: float, met: float) -> Event:
    return Event(
        type=EventType.TELEMETRY_FRAME,
        data={"channels": channels, "met": met},
        timestamp=timestamp,
    )


def state_change(vehicle_state: str, previous_state: str) -> Event:
    return Event(
        type=EventType.STATE_CHANGE,
        data={"vehicle_state": vehicle_state, "previous_state": previous_state},
    )


def maneuver_status(maneuver: str, phase: str, remaining_dv: float = 0.0) -> Event:
    return Event(
        type=EventType.MANEUVER_STATUS,
        data={"maneuver": maneuver, "phase": phase, "remaining_dv": remaining_dv},
    )


def mission_phase(phase: str, index: int, total_phases: int) -> Event:
    return Event(
        type=EventType.MISSION_PHASE,
        data={"phase": phase, "index": index, "total_phases": total_phases},
    )


def alert(severity: AlertSeverity, message: str) -> Event:
    return Event(
        type=EventType.ALERT,
        data={"severity": severity.value, "message": message},
    )


def staging_event(stage: int, remaining_stages: int) -> Event:
    return Event(
        type=EventType.STAGING,
        data={"stage": stage, "remaining_stages": remaining_stages},
    )


def soi_change(from_body: str, to_body: str) -> Event:
    return Event(
        type=EventType.SOI_CHANGE,
        data={"from": from_body, "to": to_body},
    )


def log_entry(level: str, tag: str, message: str, source: str) -> Event:
    return Event(
        type=EventType.LOG_ENTRY,
        data={"level": level, "tag": tag, "message": message, "source": source},
    )
