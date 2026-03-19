"""Lambert problem solver — universal variable formulation with Stumpff functions."""

import math

import numpy as np
from numpy.typing import NDArray


def stumpff_c2(psi: float) -> float:
    """Stumpff function c2(psi)."""
    if psi > 1e-6:
        sp = math.sqrt(psi)
        return (1.0 - math.cos(sp)) / psi
    elif psi < -1e-6:
        sp = math.sqrt(-psi)
        return (math.cosh(sp) - 1.0) / (-psi)
    else:
        return 1.0 / 2.0


def stumpff_c3(psi: float) -> float:
    """Stumpff function c3(psi)."""
    if psi > 1e-6:
        sp = math.sqrt(psi)
        return (sp - math.sin(sp)) / (psi * sp)
    elif psi < -1e-6:
        sp = math.sqrt(-psi)
        return (math.sinh(sp) - sp) / ((-psi) * sp)
    else:
        return 1.0 / 6.0


def _lambert_F_y(
    z: float, r1: float, r2: float, A: float, sqrt_mu: float, tof: float
) -> tuple[float | None, float | None]:
    """Compute F(z) and y(z) for Lambert iteration."""
    c2 = stumpff_c2(z)
    c3 = stumpff_c3(z)

    sqrt_c2 = math.sqrt(c2) if c2 > 0 else math.sqrt(abs(c2))
    if sqrt_c2 < 1e-15:
        return None, None

    y = r1 + r2 + A * (z * c3 - 1.0) / sqrt_c2
    if y < 0:
        return None, None

    chi = math.sqrt(y / c2)
    F = chi**3 * c3 + A * math.sqrt(y) - sqrt_mu * tof
    return F, y


def solve_lambert(
    r1_vec: NDArray[np.float64],
    r2_vec: NDArray[np.float64],
    tof: float,
    mu: float,
    prograde: bool = True,
    max_iter: int = 200,
    tol: float = 1e-10,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Solve Lambert's problem using the universal variable method.

    Given two position vectors and a time of flight, find the orbit connecting them.

    Args:
        r1_vec: Initial position vector (m)
        r2_vec: Final position vector (m)
        tof: Time of flight (s)
        mu: Gravitational parameter (m^3/s^2)
        prograde: True for prograde transfer, False for retrograde

    Returns:
        (v1_vec, v2_vec): Departure and arrival velocity vectors (m/s)
    """
    r1 = float(np.linalg.norm(r1_vec))
    r2 = float(np.linalg.norm(r2_vec))

    cross = np.cross(r1_vec, r2_vec)
    cos_dnu = float(np.dot(r1_vec, r2_vec) / (r1 * r2))
    cos_dnu = max(-1.0, min(1.0, cos_dnu))

    if prograde:
        sin_dnu = math.sqrt(1.0 - cos_dnu**2) if cross[2] >= 0 else -math.sqrt(1.0 - cos_dnu**2)
    else:
        sin_dnu = math.sqrt(1.0 - cos_dnu**2) if cross[2] < 0 else -math.sqrt(1.0 - cos_dnu**2)

    A = sin_dnu * math.sqrt(r1 * r2 / (1.0 - cos_dnu))
    sqrt_mu = math.sqrt(mu)

    # Newton-Raphson iteration for z using numerical derivative
    z = 0.0
    for _ in range(max_iter):
        F, y = _lambert_F_y(z, r1, r2, A, sqrt_mu, tof)

        if F is None:
            z += 0.5
            continue

        if abs(F) < tol * sqrt_mu * tof:
            break

        # Numerical derivative (central difference)
        h = max(abs(z) * 1e-7, 1e-7)
        Fp, _ = _lambert_F_y(z + h, r1, r2, A, sqrt_mu, tof)
        Fm, _ = _lambert_F_y(z - h, r1, r2, A, sqrt_mu, tof)

        if Fp is not None and Fm is not None:
            dF = (Fp - Fm) / (2.0 * h)
        elif Fp is not None:
            dF = (Fp - F) / h
        else:
            break

        if abs(dF) < 1e-20:
            break

        z_new = z - F / dF
        if abs(z_new - z) < tol:
            z = z_new
            break
        z = z_new

    # Compute Lagrange coefficients
    c2 = stumpff_c2(z)
    c3 = stumpff_c3(z)
    y = r1 + r2 + A * (z * c3 - 1.0) / math.sqrt(c2)

    f = 1.0 - y / r1
    g_dot = 1.0 - y / r2
    g = A * math.sqrt(y / mu)

    v1_vec = (r2_vec - f * r1_vec) / g
    v2_vec = (g_dot * r2_vec - r1_vec) / g

    return v1_vec, v2_vec
