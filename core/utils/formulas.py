"""
Formulas for calculating various physical quantities.
"""

import math


def gravity_local(μ: float, r: float) -> float:
    """
    Calculate the local gravitational acceleration at a given radius.

    Args:
        μ: The gravitational parameter of the body
        r: The radius from the body's center

    Formula:
        g = μ / r²

    Returns:
        The local gravitational acceleration [m/s²]
    """
    g = μ / r**2
    return g


def thrust_to_weight(F_thrust: float, m: float, g: float) -> float:
    """
    Calculate the thrust-to-weight ratio.

    Args:
        F_thrust: The available thrust of the vessel
        m: The mass of the vessel
        g: The local gravitational acceleration

    Formula:
        TWR = F_thrust / (m * g)

    Returns:
        The thrust-to-weight ratio [dimensionless]
    """
    twr = F_thrust / (m * g)
    return twr


def acceleration(F_thrust: float, m: float) -> float:
    """
    Calculate the acceleration of the vessel.

    Args:
        F_thrust: The available thrust of the vessel
        m: The mass of the vessel

    Formula:
        a = F_thrust / m

    Returns:
        The acceleration of the vessel [m/s²]
    """
    a = F_thrust / m
    return a


def surface_gravity(μ: float, r: float) -> float:
    """
    Calculate the surface gravity of a body.

    Args:
        μ: The gravitational parameter of the body
        r: The radius of the body

    Formula:
        g0 = μ / r²

    Returns:
        The surface gravity of the body [m/s²]
    """
    g0 = μ / r**2
    return g0


def vis_viva(μ: float, r: float, a: float) -> float:
    """
    Instantaneous orbital velocity (vis-viva equation).

    Args:
        μ: The gravitational parameter of the body
        r: The radius of the body
        a: The semi-major axis of the orbit

    Formula:
        v = sqrt(μ * (2 / r - 1 / a))

    Returns:
        The vis-viva velocity of the body [m/s]
    """
    v = math.sqrt(μ * (2 / r - 1 / a))
    return v


def calculate_propellant_mass_flow_rate(F: float, Isp: float, g0: float) -> float:
    """Calculate the propellant mass flow rate.

    Args:
        F: The available thrust of the vessel
        Isp: The specific impulse of the active engine setup
        g0: The local standard gravity

    Returns:
        The propellant mass flow rate [kg/s]

    Formula:
        ṁ = F / (Isp * g0)
    """
    m_dot = F / (Isp * g0)
    return m_dot


def calculate_burn_time(
    m_dot: float, m0: float, delta_v: float, Isp: float, g0: float
) -> float:
    """Estimate engine burn duration via the ideal rocket equation.

    Parameters
    ----------
    g0 : float
        Standard gravitational acceleration at the body surface \(\approx 9.81\,\text{m/s}^2\) in \(\text{m/s}^2\).
    F : float
        Current available thrust of the vessel in newtons \(N\).
    Isp : float
        Specific impulse of the active engine setup in seconds \(s\).
    m0 : float
        Vessel mass at the **start** of the burn in kilograms \(kg\).
    delta_v : float
        Target velocity change for the maneuver in metres per second \(m/s\).

    Returns
    -------
    float
        Estimated burn time in seconds.

    Notes
    -----
    The calculation proceeds as follows::

        m1 = m0 / exp(Δv / (Isp · g0))        # post-burn mass
        ṁ  = F / (Isp · g0)                   # propellant mass-flow rate
        t  = (m0 − m1) / ṁ                    # burn duration

    An exception is raised if *F* ≤ 0, indicating no active engines.
    """

    m1 = m0 / math.exp(delta_v / (Isp * g0))

    burn_time = (m0 - m1) / m_dot
    return burn_time


def dr_dt(v: float, gamma: float) -> float:
    """Radial velocity component :math:`\dot r = v \sin\gamma`."""
    return v * math.sin(gamma)


def dgamma_dt(
    v: float,
    r: float,
    gamma: float,
    μ: float,
    T: float,
    m: float,
    *,
    alpha: float = 0.0,
    L: float = 0.0,
) -> float:
    """Flight-path angle rate according to the full gravity-turn model.

    Implements ::

        dγ/dt = v/r · cosγ − μ/(r² v) · cosγ + T/(m v) · cosα + L/(m v)
    """
    return (
        (v / r) * math.cos(gamma)
        - (μ / (r**2 * v)) * math.cos(gamma)
        + (T / (m * v)) * math.cos(alpha)
        + (L / (m * v))
    )


def dv_dt(
    T: float,
    m: float,
    g_r: float,
    gamma: float,
    *,
    D: float = 0.0,
) -> float:
    """Velocity magnitude rate :: dv/dt = T/m − g(r)·sinγ − D/m."""
    return T / m - g_r * math.sin(gamma) - D / m


def dm_dt(m_dot: float) -> float:
    """Vehicle mass rate – mass *decreases* with positive :pycode:`m_dot`."""
    return -m_dot


def clamp(x: float, lo: float, hi: float) -> float:
    """Return *x* clamped to the inclusive range [lo, hi]."""
    return max(lo, min(hi, x))


def calculate_phase_angle(r1: float, r2: float) -> float:
    """Calculate the phase angle between two bodies in a circular orbit.

    Args:
        r1: The radius of the first body
        r2: The radius of the second body

    Returns:
        The phase angle [rad]
    """

    phase_angle = math.pi * (1 - math.sqrt((8 * r1**3) / ((r1 + r2) ** 3)))
    return phase_angle


def get_current_phase_angle(vsl, origin, target) -> float:
    """Get the current phase angle between the vessel and the target.

    Args:
        vsl: The vessel
        origin: The origin
        target: The target

    Returns:
        The current phase angle [rad]
    """

    vessel_pos = vsl.position(origin.non_rotating_reference_frame)
    target_pos = target.position(origin.non_rotating_reference_frame)
    vessel_angle = math.atan2(vessel_pos[1], vessel_pos[0])
    target_angle = math.atan2(target_pos[1], target_pos[0])
    current_phase = (target_angle - vessel_angle) % (2 * math.pi)
    return current_phase


def calculate_lead_angle(r1: float, r2: float) -> float:
    """Calculate the lead angle between the vessel and the target.

    Args:
        r1: The radius of the first body
        r2: The radius of the second body

    Returns:
        The lead angle [rad]
    """

    alpha = (math.pi / 2) - math.sqrt(math.pow(r1 + r2, 3) / (2 * r2**3))
    return alpha
