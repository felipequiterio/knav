"""Tests for Keplerian orbit math against known KSP values."""

import math

import pytest

from knav.astro.kepler import (
    circular_velocity,
    eccentric_anomaly_from_mean,
    eccentric_anomaly_from_true,
    escape_velocity,
    gravity_local,
    mean_anomaly_from_eccentric,
    mean_motion,
    orbital_period,
    radius_at_true_anomaly,
    specific_angular_momentum,
    specific_orbital_energy,
    sphere_of_influence,
    surface_gravity,
    time_since_periapsis,
    true_anomaly_from_eccentric,
    velocity_at_true_anomaly,
    vis_viva,
)

# Kerbin constants (stock KSP)
MU_KERBIN = 3.5316e12
R_KERBIN = 600_000
SOI_KERBIN = 84_159_286
ORBITAL_R_KERBIN = 13_599_840_256  # from Kerbol

# Mun constants
MU_MUN = 6.5138398e10
R_MUN = 200_000
ORBITAL_R_MUN = 12_000_000  # from Kerbin
PERIOD_MUN = 138_984.38

# Kerbol
MU_KERBOL = 1.1723328e18

# Standard LKO: 100km altitude = 700,000m radius from Kerbin center
LKO_RADIUS = R_KERBIN + 100_000  # 700,000 m
LKO_VELOCITY = 2246.0  # approximately 2246 m/s


class TestVisViva:
    def test_circular_orbit(self):
        """For a circular orbit, vis-viva should equal sqrt(mu/r)."""
        v = vis_viva(MU_KERBIN, LKO_RADIUS, LKO_RADIUS)
        v_circ = math.sqrt(MU_KERBIN / LKO_RADIUS)
        assert v == pytest.approx(v_circ, rel=1e-10)

    def test_lko_velocity(self):
        """LKO at 100km should be approximately 2246 m/s."""
        v = vis_viva(MU_KERBIN, LKO_RADIUS, LKO_RADIUS)
        assert v == pytest.approx(LKO_VELOCITY, rel=0.01)

    def test_elliptical_apoapsis_slower(self):
        """At apoapsis, velocity should be less than circular."""
        a = (LKO_RADIUS + 12_000_000) / 2  # Mun transfer orbit
        v_apo = vis_viva(MU_KERBIN, 12_000_000, a)
        v_circ = circular_velocity(MU_KERBIN, 12_000_000)
        assert v_apo < v_circ


class TestCircularVelocity:
    def test_lko(self):
        v = circular_velocity(MU_KERBIN, LKO_RADIUS)
        assert v == pytest.approx(LKO_VELOCITY, rel=0.01)


class TestEscapeVelocity:
    def test_escape_greater_than_circular(self):
        v_esc = escape_velocity(MU_KERBIN, LKO_RADIUS)
        v_circ = circular_velocity(MU_KERBIN, LKO_RADIUS)
        assert v_esc == pytest.approx(v_circ * math.sqrt(2), rel=1e-10)


class TestOrbitalPeriod:
    def test_lko_period(self):
        """LKO at 100km should have period ~1950-2000s."""
        T = orbital_period(MU_KERBIN, LKO_RADIUS)
        assert 1900 < T < 2100

    def test_mun_orbit(self):
        """Mun orbital period should match known value ~138,984s."""
        T = orbital_period(MU_KERBIN, ORBITAL_R_MUN)
        assert T == pytest.approx(PERIOD_MUN, rel=0.01)


class TestMeanMotion:
    def test_circular_orbit(self):
        n = mean_motion(MU_KERBIN, LKO_RADIUS)
        T = orbital_period(MU_KERBIN, LKO_RADIUS)
        assert n == pytest.approx(2 * math.pi / T, rel=1e-10)


class TestSpecificEnergy:
    def test_bound_orbit_negative(self):
        """Bound orbit should have negative specific energy."""
        eps = specific_orbital_energy(MU_KERBIN, LKO_RADIUS)
        assert eps < 0


class TestSpecificAngularMomentum:
    def test_circular_orbit(self):
        """For e=0, h = sqrt(mu * a)."""
        h = specific_angular_momentum(MU_KERBIN, LKO_RADIUS, 0.0)
        assert h == pytest.approx(math.sqrt(MU_KERBIN * LKO_RADIUS), rel=1e-10)


class TestRadiusAtTrueAnomaly:
    def test_periapsis(self):
        """At nu=0 (periapsis), r = a(1-e)."""
        e = 0.3
        a = 1_000_000
        r = radius_at_true_anomaly(a, e, 0.0)
        assert r == pytest.approx(a * (1 - e), rel=1e-10)

    def test_apoapsis(self):
        """At nu=pi (apoapsis), r = a(1+e)."""
        e = 0.3
        a = 1_000_000
        r = radius_at_true_anomaly(a, e, math.pi)
        assert r == pytest.approx(a * (1 + e), rel=1e-10)

    def test_circular(self):
        """For e=0, radius is constant."""
        r = radius_at_true_anomaly(LKO_RADIUS, 0.0, 1.234)
        assert r == pytest.approx(LKO_RADIUS, rel=1e-10)


class TestVelocityAtTrueAnomaly:
    def test_circular_orbit_no_radial(self):
        """Circular orbit should have zero radial velocity."""
        vr, vt = velocity_at_true_anomaly(MU_KERBIN, LKO_RADIUS, 0.0, 1.0)
        assert vr == pytest.approx(0.0, abs=1e-6)

    def test_circular_orbit_transverse(self):
        """Circular orbit transverse velocity should match circular velocity."""
        vr, vt = velocity_at_true_anomaly(MU_KERBIN, LKO_RADIUS, 0.0, 0.0)
        v_circ = circular_velocity(MU_KERBIN, LKO_RADIUS)
        assert vt == pytest.approx(v_circ, rel=1e-10)


class TestKeplerEquation:
    def test_roundtrip_M_E(self):
        """M -> E -> M should be identity."""
        e = 0.5
        M_original = 1.5
        E = eccentric_anomaly_from_mean(M_original, e)
        M_back = mean_anomaly_from_eccentric(E, e)
        assert M_back == pytest.approx(M_original, rel=1e-9)

    def test_roundtrip_nu_E(self):
        """nu -> E -> nu should be identity."""
        e = 0.4
        nu_original = 2.0
        E = eccentric_anomaly_from_true(nu_original, e)
        nu_back = true_anomaly_from_eccentric(E, e)
        assert nu_back == pytest.approx(nu_original, rel=1e-9)

    def test_circular_orbit_E_equals_M(self):
        """For e=0, E should equal M."""
        M = 1.0
        E = eccentric_anomaly_from_mean(M, 0.0)
        assert E == pytest.approx(M, rel=1e-10)

    def test_high_eccentricity(self):
        """Solver should converge for high eccentricity."""
        e = 0.95
        M = 0.5
        E = eccentric_anomaly_from_mean(M, e)
        M_back = mean_anomaly_from_eccentric(E, e)
        assert M_back == pytest.approx(M, rel=1e-8)


class TestTimeSincePeriapsis:
    def test_half_period_at_apoapsis(self):
        """At nu=pi (apoapsis), time should be half the period."""
        T = orbital_period(MU_KERBIN, LKO_RADIUS)
        t = time_since_periapsis(MU_KERBIN, LKO_RADIUS, 0.001, math.pi)
        assert t == pytest.approx(T / 2, rel=0.01)


class TestGravity:
    def test_kerbin_surface_gravity(self):
        g = surface_gravity(MU_KERBIN, R_KERBIN)
        assert g == pytest.approx(9.81, rel=0.01)

    def test_gravity_decreases_with_altitude(self):
        g_surface = gravity_local(MU_KERBIN, R_KERBIN)
        g_orbit = gravity_local(MU_KERBIN, LKO_RADIUS)
        assert g_orbit < g_surface


class TestSOI:
    def test_soi_formula(self):
        """SOI formula with mass ratio."""
        # Approximate test: Kerbin mass from mu, Kerbol mass from mu
        soi = sphere_of_influence(ORBITAL_R_KERBIN, MU_KERBIN, MU_KERBOL)
        assert soi == pytest.approx(SOI_KERBIN, rel=0.05)
