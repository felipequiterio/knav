"""Stream lifecycle manager for KRPC telemetry."""

from __future__ import annotations

from typing import Any

import structlog

from knav.krpc_interface.errors import StreamError

log = structlog.get_logger()


class StreamManager:
    """Creates, reads, and tears down KRPC telemetry streams."""

    def __init__(self) -> None:
        self._streams: dict[str, Any] = {}

    @property
    def is_initialized(self) -> bool:
        return len(self._streams) > 0

    def initialize(self, conn, vessel) -> None:
        """Create all telemetry streams for the given vessel.

        On partial failure the already-created streams are torn down and a
        ``StreamError`` is raised.
        """
        body = vessel.orbit.body
        flight_srf = vessel.flight(body.reference_frame)
        flight_inr = vessel.flight(body.non_rotating_reference_frame)
        orbit = vessel.orbit
        sc = conn.space_center

        stream_defs: list[tuple[str, Any, str]] = [
            # Time
            ("ut", sc, "ut"),
            ("met", vessel, "met"),
            # Position (surface-relative flight)
            ("altitude_mean", flight_srf, "mean_altitude"),
            ("altitude_surface", flight_srf, "surface_altitude"),
            ("latitude", flight_srf, "latitude"),
            ("longitude", flight_srf, "longitude"),
            # Orbit (17 fields)
            ("apoapsis", orbit, "apoapsis"),
            ("periapsis", orbit, "periapsis"),
            ("apoapsis_altitude", orbit, "apoapsis_altitude"),
            ("periapsis_altitude", orbit, "periapsis_altitude"),
            ("semi_major_axis", orbit, "semi_major_axis"),
            ("eccentricity", orbit, "eccentricity"),
            ("inclination", orbit, "inclination"),
            ("longitude_of_ascending_node", orbit, "longitude_of_ascending_node"),
            ("argument_of_periapsis", orbit, "argument_of_periapsis"),
            ("true_anomaly", orbit, "true_anomaly"),
            ("mean_anomaly", orbit, "mean_anomaly"),
            ("period", orbit, "period"),
            ("time_to_apoapsis", orbit, "time_to_apoapsis"),
            ("time_to_periapsis", orbit, "time_to_periapsis"),
            ("radius", orbit, "radius"),
            ("speed", orbit, "speed"),
            ("body_name", orbit.body, "name"),
            # Velocity
            ("speed_orbital", flight_inr, "speed"),
            ("vertical_speed", flight_inr, "vertical_speed"),
            ("horizontal_speed", flight_inr, "horizontal_speed"),
            ("speed_surface", flight_srf, "speed"),
            # Attitude (surface-relative)
            ("pitch", flight_srf, "pitch"),
            ("heading", flight_srf, "heading"),
            ("roll", flight_srf, "roll"),
            # Aero
            ("dynamic_pressure", flight_srf, "dynamic_pressure"),
            ("mach", flight_srf, "mach_number"),
            ("g_force", flight_srf, "g_force"),
            # Mass
            ("mass", vessel, "mass"),
            ("dry_mass", vessel, "dry_mass"),
            # Propulsion
            ("available_thrust", vessel, "available_thrust"),
            ("max_thrust", vessel, "max_thrust"),
            ("specific_impulse", vessel, "specific_impulse"),
            # Identity
            ("name", vessel, "name"),
            ("situation", vessel, "situation"),
        ]

        for name, source, attr in stream_defs:
            try:
                self._streams[name] = conn.add_stream(getattr, source, attr)
            except Exception as exc:
                log.error("stream.create_failed", stream=name, exc_info=True)
                self.teardown()
                raise StreamError(f"Failed to create stream {name!r}", original=exc) from exc

        log.info("streams.initialized", count=len(self._streams))

    def get(self, name: str) -> Any:
        """Read a single stream value by name."""
        stream = self._streams.get(name)
        if stream is None:
            raise StreamError(f"Stream {name!r} not found")
        return stream()

    def read_all(self) -> dict[str, Any]:
        """Read every stream; on per-stream error set value to None and log."""
        result: dict[str, Any] = {}
        for name, stream in self._streams.items():
            try:
                result[name] = stream()
            except Exception:
                log.warning("stream.read_error", stream=name, exc_info=True)
                result[name] = None
        return result

    def teardown(self) -> None:
        """Remove all active streams."""
        for name, stream in self._streams.items():
            try:
                stream.remove()
            except Exception:
                log.warning("stream.remove_error", stream=name, exc_info=True)
        self._streams.clear()
        log.info("streams.teardown")

    def refresh_vessel(self, conn, vessel) -> None:
        """Tear down existing streams and re-initialize for a new vessel."""
        self.teardown()
        self.initialize(conn, vessel)
