"""
Formulas for calculating various physical quantities.
"""

import math
from typing import Tuple


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


def delta_v_hohmann(mu: float, r1: float, r2: float) -> Tuple[float, float]:
    """Return the two classical Hohmann ∆v legs.

    Args:
        mu: The gravitational parameter of the body
        r1: The radius of the initial circular orbit
        r2: The radius of the target circular orbit

    Returns:
        The two classical Hohmann ∆v legs
        dv1: The ∆v for the first burn
        dv2: The ∆v for the second burn

    Formula:
        dv1 = sqrt(mu / r1) * (sqrt(2 * r2 / (r1 + r2)) - 1)
        dv2 = sqrt(mu / r2) * (1 - sqrt(2 * r1 / (r1 + r2)))
    """

    dv1 = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    dv2 = math.sqrt(mu / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))

    return dv1, dv2


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


def calculate_transfer_time(mu: float, r1: float, r2: float) -> float:
    """Calculate the transfer time for a Hohmann transfer.

    Args:
        mu: The gravitational parameter of the body
        r1: The radius of the initial circular orbit
        r2: The radius of the target circular orbit

    Returns:
        The transfer time [s]

    Formula:
        t = π * sqrt((r2 + r1)**3 / (8 * mu))
    """
    transfer_time = math.pi * math.sqrt((r2 + r1) ** 3 / (8 * mu))
    return transfer_time


def calculate_target_period(mu: float, r2: float) -> float:
    """Calculate the target period for a Hohmann transfer.

    Args:
        mu: The gravitational parameter of the body
        r2: The radius of the target circular orbit

    Returns:
        The target period [s]

    Formula:
        T = 2π * sqrt(r2**3 / mu)
    """
    target_period = 2 * math.pi * math.sqrt(r2**3 / mu)
    return target_period


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


def gravity_turn_derivatives(
    t: float,
    state: Tuple[float, float, float, float],
    *,
    μ: float,
    T: float,
    m_dot: float,
    α: float = 0.0,
    L: float = 0.0,
    D: float = 0.0,
) -> Tuple[float, float, float, float]:
    """Compute the time-derivatives for the core gravity-turn ODE system.

    The state vector is interpreted as **(r, γ, v, m)** where

    * ``r`` – radial distance from the centre of the body [m]
    * ``γ`` – flight-path angle measured from the local horizontal [rad]
    * ``v`` – inertial velocity magnitude [m/s]
    * ``m`` – instantaneous vehicle mass [kg]

    Parameters
    ----------
    t : float
        Time since launch [s]. (Unused – present for scipy ODE-solver compatibility.)
    state : Tuple[float, float, float, float]
        Current state vector ``(r, γ, v, m)``.
    μ : float
        Gravitational parameter of the central body (\(μ = G·M\)) [m³/s²].
    T : float
        Thrust magnitude assumed *constant* over the integration step [N].
    m_dot : float
        Propellant mass-flow rate *magnitude* (positive) [kg/s].  The vehicle mass
        therefore decreases at a rate ``dm/dt = −m_dot``.
    α : float, optional
        Engine gimbal angle *relative to the velocity vector* [rad].  ``α = 0``
        corresponds to thrust aligned with the velocity (classical gravity turn).
    L : float, optional
        Aerodynamic lift magnitude [N].  Can be set to zero when neglected.
    D : float, optional
        Aerodynamic drag magnitude [N].  Can be set to zero when neglected.

    Returns
    -------
    Tuple[float, float, float, float]
        The derivatives ``(dr/dt, dγ/dt, dv/dt, dm/dt)``.

    Notes
    -----
    The governing equations implemented are (see *Kerbal Space Program* lore and
    standard launch dynamics references) ::

        dr/dt     = v · sin(γ)
        dγ/dt     =  v/r · cos(γ) − μ/(r² v) · cos(γ) + T/(m v) · cos(α) + L/(m v)
        dv/dt     =  T/m − g(r) · sin(γ) − D/m
        dm/dt     = −ṁ

    where ``g(r) = μ / r²``.
    """

    # Unpack the state vector ---------------------------------------------------------
    r, gamma, v, m = state

    # Guard against numerical singularities ------------------------------------------
    if r <= 0:
        raise ValueError("Radius must be positive and non-zero.")
    if v <= 0:
        raise ValueError(
            "Velocity must be positive and non-zero to evaluate derivatives."
        )
    if m <= 0:
        raise ValueError(
            "Vehicle mass became non-positive, check inputs/solver settings."
        )

    # Local gravity (scalar magnitude)
    g_r = gravity_local(μ, r)

    # Core derivatives ----------------------------------------------------------------
    r_dot = v * math.sin(gamma)

    gamma_dot = (
        (v / r) * math.cos(gamma)
        - (μ / (r**2 * v)) * math.cos(gamma)
        + (T / (m * v)) * math.cos(α)
        + (L / (m * v))
    )

    v_dot = T / m - g_r * math.sin(gamma) - D / m

    m_dot_dt = -m_dot

    return r_dot, gamma_dot, v_dot, m_dot_dt


def gravity_turn_simplified_derivatives(
    t: float,
    state: Tuple[float, float, float, float],
    *,
    μ: float,
    T: float,
    m_dot: float,
) -> Tuple[float, float, float, float]:
    """A thin wrapper around :func:`gravity_turn_derivatives` for the classic
    gravity-turn assumption (thrust perfectly aligned with velocity, no lift/drag).
    """

    return gravity_turn_derivatives(
        t,
        state,
        μ=μ,
        T=T,
        m_dot=m_dot,
        α=0.0,
        L=0.0,
        D=0.0,
    )


def clamp(x: float, lo: float, hi: float) -> float:
    """Return *x* clamped to the inclusive range [lo, hi]."""
    return max(lo, min(hi, x))
