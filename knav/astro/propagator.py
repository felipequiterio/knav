"""Orbit propagation — universal variable formulation."""

import math

import numpy as np
from numpy.typing import NDArray

from knav.astro.lambert import stumpff_c2, stumpff_c3


def propagate_kepler(
    mu: float,
    r0: NDArray[np.float64],
    v0: NDArray[np.float64],
    dt: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Propagate a Keplerian orbit using the universal variable formulation.

    Based on Algorithm 3.4 from Curtis, "Orbital Mechanics for Engineering Students".

    Args:
        mu: Gravitational parameter (m^3/s^2)
        r0: Initial position vector (m)
        v0: Initial velocity vector (m/s)
        dt: Time step (s)

    Returns:
        (r_final, v_final): Position and velocity vectors at time t0 + dt
    """
    r0_mag = float(np.linalg.norm(r0))
    v0_mag = float(np.linalg.norm(v0))
    sqrt_mu = math.sqrt(mu)

    # sigma0 = dot(r0, v0) / sqrt(mu)
    sigma0 = float(np.dot(r0, v0)) / sqrt_mu

    # alpha = 1/a (reciprocal of semi-major axis)
    alpha = 2.0 / r0_mag - v0_mag**2 / mu

    # Initial guess for universal variable chi
    if alpha > 1e-10:  # elliptical
        chi = sqrt_mu * dt * alpha
    elif alpha < -1e-10:  # hyperbolic
        a = 1.0 / alpha
        chi = (
            math.copysign(1.0, dt)
            * math.sqrt(-1.0 / alpha)
            * math.log(
                (-2.0 * mu * alpha * dt)
                / (
                    float(np.dot(r0, v0))
                    + math.copysign(1.0, dt) * math.sqrt(-mu / alpha) * (1.0 - r0_mag * alpha)
                )
            )
        )
    else:  # parabolic
        h = np.cross(r0, v0)
        p = float(np.dot(h, h)) / mu
        s = 0.5 * math.atan2(1.0, 3.0 * math.sqrt(mu / p**3) * dt)
        w = math.atan(math.tan(s) ** (1.0 / 3.0))
        chi = math.sqrt(p) * 2.0 / math.tan(2.0 * w)

    # Newton-Raphson: solve F(chi) = 0
    # F(chi) = (1-alpha*r0)*chi^3*c3 + sigma0*chi^2*c2 + r0*chi - sqrt(mu)*dt
    # F'(chi) = r(chi) = chi^2*c2 + sigma0*chi*(1-z*c3) + r0*(1-z*c2)
    one_minus_ar0 = 1.0 - alpha * r0_mag
    for _ in range(max_iter):
        chi2 = chi * chi
        z = alpha * chi2
        c2 = stumpff_c2(z)
        c3 = stumpff_c3(z)

        F = one_minus_ar0 * chi2 * chi * c3 + sigma0 * chi2 * c2 + r0_mag * chi - sqrt_mu * dt
        r = chi2 * c2 + sigma0 * chi * (1.0 - z * c3) + r0_mag * (1.0 - z * c2)

        if abs(r) < 1e-15:
            break

        dchi = F / r
        chi = chi - dchi

        if abs(dchi) < tol:
            break

    # Final Lagrange coefficients
    chi2 = chi * chi
    z = alpha * chi2
    c2 = stumpff_c2(z)
    c3 = stumpff_c3(z)

    f = 1.0 - chi2 / r0_mag * c2
    g = dt - chi2 * chi / sqrt_mu * c3

    r_final = f * r0 + g * v0
    r_mag = float(np.linalg.norm(r_final))

    f_dot = sqrt_mu / (r_mag * r0_mag) * chi * (z * c3 - 1.0)
    g_dot = 1.0 - chi2 / r_mag * c2

    v_final = f_dot * r0 + g_dot * v0

    return r_final, v_final


def propagate_to_true_anomaly(
    mu: float,
    a: float,
    e: float,
    i: float,
    omega: float,
    Omega: float,
    nu0: float,
    nu_target: float,
) -> float:
    """Compute the time of flight between two true anomalies.

    Args:
        mu: Gravitational parameter
        a: Semi-major axis
        e: Eccentricity
        i: Inclination (unused, for API completeness)
        omega: Argument of periapsis (unused)
        Omega: LAN (unused)
        nu0: Initial true anomaly (rad)
        nu_target: Target true anomaly (rad)

    Returns:
        Time of flight (seconds)
    """
    from knav.astro.kepler import (
        eccentric_anomaly_from_true,
        mean_anomaly_from_eccentric,
        mean_motion,
    )

    E0 = eccentric_anomaly_from_true(nu0, e)
    E1 = eccentric_anomaly_from_true(nu_target, e)

    M0 = mean_anomaly_from_eccentric(E0, e)
    M1 = mean_anomaly_from_eccentric(E1, e)

    dM = M1 - M0
    if dM < 0:
        dM += 2.0 * math.pi

    n = mean_motion(mu, a)
    return dM / n
