"""Tests for Lambert solver."""

import math

import numpy as np
import pytest

from knav.astro.kepler import circular_velocity, orbital_period
from knav.astro.lambert import solve_lambert, stumpff_c2, stumpff_c3

MU_KERBIN = 3.5316e12


class TestStumpff:
    def test_c2_positive_psi(self):
        """c2(psi) for positive psi (elliptical)."""
        c2 = stumpff_c2(1.0)
        expected = (1.0 - math.cos(1.0)) / 1.0
        assert c2 == pytest.approx(expected, rel=1e-10)

    def test_c3_positive_psi(self):
        c3 = stumpff_c3(1.0)
        expected = (1.0 - math.sin(1.0)) / 1.0
        assert c3 == pytest.approx(expected, rel=1e-10)

    def test_c2_zero(self):
        assert stumpff_c2(0.0) == pytest.approx(0.5, rel=1e-10)

    def test_c3_zero(self):
        assert stumpff_c3(0.0) == pytest.approx(1.0 / 6.0, rel=1e-10)

    def test_c2_negative_psi(self):
        """c2(psi) for negative psi (hyperbolic)."""
        c2 = stumpff_c2(-1.0)
        expected = (math.cosh(1.0) - 1.0) / 1.0
        assert c2 == pytest.approx(expected, rel=1e-10)


class TestLambert:
    def test_circular_orbit_90_transfer(self):
        """Lambert for a 90-degree transfer in a circular orbit should recover
        the circular velocity magnitude."""
        r = 700_000  # LKO radius
        v_circ = circular_velocity(MU_KERBIN, r)

        # Two points 90 degrees apart (avoids 180-degree degeneracy)
        r1 = np.array([r, 0.0, 0.0])
        r2 = np.array([0.0, r, 0.0])
        tof = orbital_period(MU_KERBIN, r) / 4.0

        v1, v2 = solve_lambert(r1, r2, tof, MU_KERBIN, prograde=True)

        speed1 = float(np.linalg.norm(v1))
        assert speed1 == pytest.approx(v_circ, rel=0.01)

    def test_returns_correct_shapes(self):
        r1 = np.array([700_000.0, 0.0, 0.0])
        r2 = np.array([0.0, 700_000.0, 0.0])
        tof = orbital_period(MU_KERBIN, 700_000) / 4.0

        v1, v2 = solve_lambert(r1, r2, tof, MU_KERBIN)
        assert v1.shape == (3,)
        assert v2.shape == (3,)
