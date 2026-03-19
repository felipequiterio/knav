from pydantic import BaseModel


class OrbitState(BaseModel):
    body_name: str
    apoapsis: float
    periapsis: float
    apoapsis_altitude: float
    periapsis_altitude: float
    semi_major_axis: float
    eccentricity: float
    inclination: float
    longitude_of_ascending_node: float
    argument_of_periapsis: float
    true_anomaly: float
    mean_anomaly: float
    period: float
    time_to_apoapsis: float
    time_to_periapsis: float
    radius: float
    speed: float


class OrbitalElements(BaseModel):
    """Pure math orbital elements — no KRPC dependency."""

    a: float  # semi-major axis (m)
    e: float  # eccentricity
    i: float  # inclination (rad)
    omega: float  # argument of periapsis (rad)
    Omega: float  # longitude of ascending node (rad)
    nu: float  # true anomaly (rad)
    mu: float  # gravitational parameter (m^3/s^2)
