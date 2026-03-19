"""Tests for orbit propagation."""

import math

import numpy as np
import pytest

from knav.astro.kepler import circular_velocity, orbital_period
from knav.astro.propagator import propagate_kepler, propagate_to_true_anomaly

MU_KERBIN = 3.5316e12
LKO_RADIUS = 700_000.0


class TestPropagateKepler:
    def test_circular_orbit_full_period(self):
        """After one full period, position should return to start."""
        r0 = np.array([LKO_RADIUS, 0.0, 0.0])
        v_circ = circular_velocity(MU_KERBIN, LKO_RADIUS)
        v0 = np.array([0.0, v_circ, 0.0])
        T = orbital_period(MU_KERBIN, LKO_RADIUS)

        r_f, v_f = propagate_kepler(MU_KERBIN, r0, v0, T)

        assert float(np.linalg.norm(r_f - r0)) == pytest.approx(0.0, abs=100)  # within 100m
        assert float(np.linalg.norm(v_f - v0)) == pytest.approx(0.0, abs=0.1)  # within 0.1 m/s

    def test_circular_orbit_quarter_period(self):
        """After 1/4 period, should be 90 degrees around."""
        r0 = np.array([LKO_RADIUS, 0.0, 0.0])
        v_circ = circular_velocity(MU_KERBIN, LKO_RADIUS)
        v0 = np.array([0.0, v_circ, 0.0])
        T = orbital_period(MU_KERBIN, LKO_RADIUS)

        r_f, v_f = propagate_kepler(MU_KERBIN, r0, v0, T / 4)

        # Should be roughly at (0, r, 0)
        assert abs(r_f[0]) < LKO_RADIUS * 0.05  # x near zero
        assert r_f[1] == pytest.approx(LKO_RADIUS, rel=0.01)

    def test_preserves_energy(self):
        """Specific orbital energy should be conserved."""
        r0 = np.array([LKO_RADIUS, 0.0, 0.0])
        v_circ = circular_velocity(MU_KERBIN, LKO_RADIUS)
        v0 = np.array([0.0, v_circ * 1.1, 0.0])  # slightly elliptical

        eps0 = float(np.dot(v0, v0)) / 2 - MU_KERBIN / float(np.linalg.norm(r0))

        r_f, v_f = propagate_kepler(MU_KERBIN, r0, v0, 5000)
        eps_f = float(np.dot(v_f, v_f)) / 2 - MU_KERBIN / float(np.linalg.norm(r_f))

        assert eps_f == pytest.approx(eps0, rel=1e-6)


class TestPropagateToTrueAnomaly:
    def test_half_orbit(self):
        """Time from nu=0 to nu=pi should be half the period."""
        T = orbital_period(MU_KERBIN, LKO_RADIUS)
        e = 0.001  # near-circular
        dt = propagate_to_true_anomaly(
            MU_KERBIN, LKO_RADIUS, e, 0, 0, 0, 0.0, math.pi
        )
        assert dt == pytest.approx(T / 2, rel=0.01)

    def test_full_orbit(self):
        """Time from nu=0 to nu=2*pi should be one period."""
        T = orbital_period(MU_KERBIN, LKO_RADIUS)
        e = 0.1
        # nu=0 to nu=2*pi-epsilon (just under full orbit)
        dt = propagate_to_true_anomaly(
            MU_KERBIN, LKO_RADIUS, e, 0, 0, 0, 0.0, 2 * math.pi - 0.001
        )
        assert dt == pytest.approx(T, rel=0.01)
