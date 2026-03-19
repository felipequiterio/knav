from pydantic import BaseModel

from knav.models.enums import VesselSituation
from knav.models.orbit import OrbitState


class VesselState(BaseModel):
    """Frozen snapshot of vessel state produced by Navigation each tick."""

    # Time
    timestamp_ut: float
    met: float

    # Identity
    name: str
    situation: VesselSituation
    body_name: str

    # Mass
    mass: float
    dry_mass: float

    # Position
    altitude_mean: float
    altitude_surface: float
    latitude: float
    longitude: float

    # Velocity
    speed_orbital: float
    speed_surface: float
    vertical_speed: float
    horizontal_speed: float

    # Attitude
    pitch: float
    heading: float
    roll: float

    # Aero
    dynamic_pressure: float
    mach: float
    g_force: float

    # Propulsion
    available_thrust: float
    max_thrust: float
    specific_impulse: float
    twr: float
    delta_v_remaining: float

    # Derived
    flight_path_angle: float
    local_gravity: float

    # Orbit
    orbit: OrbitState

    model_config = {"frozen": True}
