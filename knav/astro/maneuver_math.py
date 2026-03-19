"""Delta-v calculations, transfer math, and burn planning — pure functions."""

import math

from knav.astro.kepler import circular_velocity, mean_motion, vis_viva


# --- Hohmann Transfer ---


def hohmann_delta_v(mu: float, r1: float, r2: float) -> tuple[float, float]:
    """Delta-v for a Hohmann transfer between circular orbits.

    Returns (dv1, dv2) where dv1 is the departure burn and dv2 is the arrival burn.
    Both values are positive magnitudes.
    """
    dv1 = math.sqrt(mu / r1) * (math.sqrt(2.0 * r2 / (r1 + r2)) - 1.0)
    dv2 = math.sqrt(mu / r2) * (1.0 - math.sqrt(2.0 * r1 / (r1 + r2)))
    return abs(dv1), abs(dv2)


def hohmann_transfer_time(mu: float, r1: float, r2: float) -> float:
    """Transfer time for a Hohmann transfer (half the transfer orbit period)."""
    return math.pi * math.sqrt((r1 + r2) ** 3 / (8.0 * mu))


def hohmann_transfer_sma(r1: float, r2: float) -> float:
    """Semi-major axis of the Hohmann transfer orbit."""
    return (r1 + r2) / 2.0


def hohmann_phase_angle(r1: float, r2: float) -> float:
    """Required phase angle at departure for a Hohmann transfer (radians)."""
    return math.pi * (1.0 - (1.0 / (2.0 * math.sqrt(2.0))) * math.sqrt((r1 / r2 + 1.0) ** 3))


def hohmann_lead_angle(mu: float, r1: float, r2: float) -> float:
    """How far the target moves during a Hohmann transfer (radians)."""
    tof = hohmann_transfer_time(mu, r1, r2)
    w2 = mean_motion(mu, r2)
    return w2 * tof


def hohmann_phase_required(mu: float, r1: float, r2: float) -> float:
    """Required phase angle at departure (radians)."""
    return math.pi - hohmann_lead_angle(mu, r1, r2)


def hohmann_wait_time(
    mu: float, r1: float, r2: float, current_phase: float
) -> float:
    """Time to wait for correct phase angle (seconds).

    current_phase is the current phase angle in radians.
    """
    required = hohmann_phase_required(mu, r1, r2)
    w1 = mean_motion(mu, r1)
    w2 = mean_motion(mu, r2)
    synodic_rate = w1 - w2
    if abs(synodic_rate) < 1e-15:
        return 0.0
    wait = (required - current_phase) / synodic_rate
    # Ensure positive wait time (wait for next alignment if we missed this one)
    T_syn = synodic_period(mu, r1, r2)
    while wait < 0:
        wait += T_syn
    return wait


# --- Bi-Elliptic Transfer ---


def bielliptic_delta_v(
    mu: float, r1: float, r2: float, r_intermediate: float
) -> tuple[float, float, float]:
    """Delta-v for a bi-elliptic transfer.

    Returns (dv1, dv2, dv3) for the three burns.
    More efficient than Hohmann when r2/r1 > 11.94.
    """
    a1 = (r1 + r_intermediate) / 2.0
    a2 = (r2 + r_intermediate) / 2.0

    dv1 = abs(math.sqrt(2.0 * mu / r1 - mu / a1) - math.sqrt(mu / r1))
    dv2 = abs(
        math.sqrt(2.0 * mu / r_intermediate - mu / a2)
        - math.sqrt(2.0 * mu / r_intermediate - mu / a1)
    )
    dv3 = abs(math.sqrt(2.0 * mu / r2 - mu / a2) - math.sqrt(mu / r2))
    return dv1, dv2, dv3


# --- Plane Change ---


def plane_change_delta_v(v: float, delta_i: float) -> float:
    """Delta-v for a simple plane change at velocity v.

    delta_i is the inclination change in radians.
    """
    return 2.0 * v * math.sin(delta_i / 2.0)


def combined_plane_change_delta_v(
    mu: float, r: float, delta_i: float, r_target: float
) -> float:
    """Delta-v for combined plane change + orbit raise at optimal point."""
    v1 = circular_velocity(mu, r)
    v2 = circular_velocity(mu, r_target)
    return math.sqrt(v1**2 + v2**2 - 2.0 * v1 * v2 * math.cos(delta_i))


# --- Circularization ---


def circularization_delta_v(mu: float, r_circ: float, a_current: float) -> float:
    """Delta-v to circularize at r_circ from an orbit with semi-major axis a_current."""
    v_circ = circular_velocity(mu, r_circ)
    v_current = vis_viva(mu, r_circ, a_current)
    return v_circ - v_current


# --- Deorbit ---


def deorbit_delta_v(mu: float, r_current: float, r_periapsis_target: float) -> float:
    """Retrograde delta-v to lower periapsis for reentry.

    Returns a positive magnitude (burn is retrograde).
    """
    a_new = (r_current + r_periapsis_target) / 2.0
    v_current = circular_velocity(mu, r_current)
    v_new = vis_viva(mu, r_current, a_new)
    return abs(v_current - v_new)


# --- Burn Time (Tsiolkovsky) ---


def burn_time(
    delta_v: float, thrust: float, isp: float, g0: float, m0: float
) -> float:
    """Burn duration using the Tsiolkovsky rocket equation.

    Args:
        delta_v: Required delta-v (m/s)
        thrust: Engine thrust (N)
        isp: Specific impulse (s)
        g0: Standard gravity (m/s^2)
        m0: Initial mass (kg)
    """
    m1 = m0 / math.exp(delta_v / (isp * g0))
    m_dot = thrust / (isp * g0)
    if m_dot < 1e-15:
        return float("inf")
    return (m0 - m1) / m_dot


def mass_flow_rate(thrust: float, isp: float, g0: float) -> float:
    """Mass flow rate: m_dot = F / (Isp * g0)."""
    return thrust / (isp * g0)


# --- Phase Angle ---


def current_phase_angle(
    vessel_angle: float, target_angle: float
) -> float:
    """Phase angle between vessel and target (radians, 0 to 2*pi).

    Both angles are true longitude or similar angular position in a common frame.
    """
    phase = target_angle - vessel_angle
    return phase % (2.0 * math.pi)


def synodic_period(mu: float, r1: float, r2: float) -> float:
    """Synodic period between two circular orbits."""
    w1 = mean_motion(mu, r1)
    w2 = mean_motion(mu, r2)
    dw = abs(w1 - w2)
    if dw < 1e-15:
        return float("inf")
    return 2.0 * math.pi / dw


# --- Gravity Turn ODE ---


def dgamma_dt(
    v: float,
    r: float,
    gamma: float,
    mu: float,
    T: float,
    m: float,
    alpha: float = 0.0,
    L: float = 0.0,
) -> float:
    """Flight-path angle rate for gravity turn.

    Args:
        v: velocity (m/s)
        r: radius from body center (m)
        gamma: flight path angle (rad)
        mu: gravitational parameter
        T: thrust (N)
        m: mass (kg)
        alpha: angle of attack (rad)
        L: lift force (N)
    """
    if v < 1e-6:
        return 0.0
    cos_g = math.cos(gamma)
    return (
        (v / r) * cos_g
        - (mu / (r**2 * v)) * cos_g
        + (T / (m * v)) * math.cos(alpha)
        + L / (m * v)
    )


def dv_dt(T: float, m: float, g_r: float, gamma: float, D: float = 0.0) -> float:
    """Speed rate for gravity turn.

    Args:
        T: thrust (N)
        m: mass (kg)
        g_r: local gravity (m/s^2)
        gamma: flight path angle (rad)
        D: drag force (N)
    """
    return T / m - g_r * math.sin(gamma) - D / m


def dr_dt(v: float, gamma: float) -> float:
    """Radial velocity: dr/dt = v * sin(gamma)."""
    return v * math.sin(gamma)
