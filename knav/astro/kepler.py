"""Keplerian orbit math — pure functions, no KRPC dependency."""

import math


def vis_viva(mu: float, r: float, a: float) -> float:
    """Orbital velocity at radius r in orbit with semi-major axis a."""
    return math.sqrt(mu * (2.0 / r - 1.0 / a))


def circular_velocity(mu: float, r: float) -> float:
    """Circular orbital velocity at radius r."""
    return math.sqrt(mu / r)


def escape_velocity(mu: float, r: float) -> float:
    """Escape velocity at radius r."""
    return math.sqrt(2.0 * mu / r)


def orbital_period(mu: float, a: float) -> float:
    """Orbital period for semi-major axis a."""
    return 2.0 * math.pi * math.sqrt(a**3 / mu)


def mean_motion(mu: float, a: float) -> float:
    """Mean angular velocity (rad/s)."""
    return math.sqrt(mu / a**3)


def specific_orbital_energy(mu: float, a: float) -> float:
    """Specific orbital energy (epsilon = -mu / 2a)."""
    return -mu / (2.0 * a)


def specific_angular_momentum(mu: float, a: float, e: float) -> float:
    """Specific angular momentum h = sqrt(mu * a * (1 - e^2))."""
    return math.sqrt(mu * a * (1.0 - e**2))


def radius_at_true_anomaly(a: float, e: float, nu: float) -> float:
    """Radius at true anomaly nu (conic equation)."""
    return a * (1.0 - e**2) / (1.0 + e * math.cos(nu))


def velocity_at_true_anomaly(
    mu: float, a: float, e: float, nu: float
) -> tuple[float, float]:
    """Radial and transverse velocity components at true anomaly nu.

    Returns (v_radial, v_transverse).
    """
    h = specific_angular_momentum(mu, a, e)
    r = radius_at_true_anomaly(a, e, nu)
    v_radial = (mu / h) * e * math.sin(nu)
    v_transverse = h / r
    return v_radial, v_transverse


def mean_anomaly_from_eccentric(E: float, e: float) -> float:
    """Kepler's equation: M = E - e*sin(E)."""
    return E - e * math.sin(E)


def eccentric_anomaly_from_mean(M: float, e: float, tol: float = 1e-10) -> float:
    """Solve Kepler's equation for E given M (Newton-Raphson)."""
    E = M if e < 0.8 else math.pi
    for _ in range(100):
        dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
        E -= dE
        if abs(dE) < tol:
            break
    return E


def true_anomaly_from_eccentric(E: float, e: float) -> float:
    """True anomaly from eccentric anomaly."""
    return 2.0 * math.atan2(
        math.sqrt(1.0 + e) * math.sin(E / 2.0),
        math.sqrt(1.0 - e) * math.cos(E / 2.0),
    )


def eccentric_anomaly_from_true(nu: float, e: float) -> float:
    """Eccentric anomaly from true anomaly."""
    return 2.0 * math.atan2(
        math.sqrt(1.0 - e) * math.sin(nu / 2.0),
        math.sqrt(1.0 + e) * math.cos(nu / 2.0),
    )


def time_since_periapsis(mu: float, a: float, e: float, nu: float) -> float:
    """Time since periapsis passage for a given true anomaly."""
    E = eccentric_anomaly_from_true(nu, e)
    M = mean_anomaly_from_eccentric(E, e)
    n = mean_motion(mu, a)
    return M / n


def gravity_local(mu: float, r: float) -> float:
    """Local gravitational acceleration at radius r."""
    return mu / r**2


def surface_gravity(mu: float, R: float) -> float:
    """Surface gravitational acceleration."""
    return mu / R**2


def sphere_of_influence(a: float, m_body: float, m_parent: float) -> float:
    """SOI radius: r_SOI = a * (m_body / m_parent)^(2/5)."""
    return a * (m_body / m_parent) ** 0.4
