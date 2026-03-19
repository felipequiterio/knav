"""Tests for delta-v calculations and transfer math against known KSP values."""

import math

import pytest

from knav.astro.kepler import circular_velocity
from knav.astro.maneuver_math import (
    bielliptic_delta_v,
    burn_time,
    circularization_delta_v,
    current_phase_angle,
    deorbit_delta_v,
    dgamma_dt,
    dr_dt,
    dv_dt,
    hohmann_delta_v,
    hohmann_phase_angle,
    hohmann_transfer_time,
    hohmann_transfer_sma,
    hohmann_wait_time,
    mass_flow_rate,
    plane_change_delta_v,
    synodic_period,
)

MU_KERBIN = 3.5316e12
R_KERBIN = 600_000
G0 = 9.81

LKO_RADIUS = R_KERBIN + 80_000  # 680,000 m (80km LKO)
LKO_100_RADIUS = R_KERBIN + 100_000  # 700,000 m (100km LKO)
MUN_ORBIT_RADIUS = 12_000_000  # from Kerbin center


class TestHohmannTransfer:
    def test_kerbin_to_mun_dv(self):
        """Hohmann LKO (80km) -> Mun orbit radius.

        dv1 ~860 m/s (departure), dv2 ~365 m/s (arrival in Kerbin frame).
        Note: dv2 is the Kerbin-frame circularization at Mun's orbital radius,
        NOT the Mun capture burn (~220 m/s) which accounts for Mun's gravity.
        """
        dv1, dv2 = hohmann_delta_v(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert dv1 == pytest.approx(860, rel=0.05)
        assert dv2 == pytest.approx(365, rel=0.05)

    def test_total_dv_positive(self):
        dv1, dv2 = hohmann_delta_v(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert dv1 > 0
        assert dv2 > 0

    def test_transfer_time_reasonable(self):
        """Transfer time to Mun orbit radius ~26,700s."""
        t = hohmann_transfer_time(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert 20_000 < t < 35_000

    def test_transfer_sma(self):
        a_t = hohmann_transfer_sma(LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert a_t == pytest.approx((LKO_RADIUS + MUN_ORBIT_RADIUS) / 2)

    def test_phase_angle_range(self):
        """Phase angle should be between -pi and pi."""
        alpha = hohmann_phase_angle(LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert -math.pi < alpha < math.pi


class TestHohmannWait:
    def test_wait_time_positive(self):
        wait = hohmann_wait_time(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS, 0.0)
        assert wait >= 0

    def test_synodic_period_finite(self):
        T_syn = synodic_period(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS)
        assert T_syn > 0
        assert T_syn < float("inf")


class TestBielliptic:
    def test_three_burns_positive(self):
        r_int = MUN_ORBIT_RADIUS * 2
        dv1, dv2, dv3 = bielliptic_delta_v(MU_KERBIN, LKO_RADIUS, MUN_ORBIT_RADIUS, r_int)
        assert dv1 > 0
        assert dv2 > 0
        assert dv3 > 0

    def test_hohmann_better_for_small_ratio(self):
        """For r2/r1 < 11.94, Hohmann should be more efficient."""
        r1 = LKO_RADIUS
        r2 = r1 * 5  # ratio = 5, Hohmann should win
        r_int = r2 * 2

        dv_h1, dv_h2 = hohmann_delta_v(MU_KERBIN, r1, r2)
        dv_b1, dv_b2, dv_b3 = bielliptic_delta_v(MU_KERBIN, r1, r2, r_int)

        assert dv_h1 + dv_h2 < dv_b1 + dv_b2 + dv_b3


class TestPlaneChange:
    def test_zero_change(self):
        dv = plane_change_delta_v(2246.0, 0.0)
        assert dv == pytest.approx(0.0, abs=1e-10)

    def test_ninety_degrees(self):
        """90-degree plane change: dv = 2*v*sin(45) = v*sqrt(2)."""
        v = 2246.0
        dv = plane_change_delta_v(v, math.pi / 2)
        assert dv == pytest.approx(v * math.sqrt(2), rel=1e-10)


class TestCircularization:
    def test_already_circular(self):
        """Circularizing a circular orbit should need zero delta-v."""
        dv = circularization_delta_v(MU_KERBIN, LKO_RADIUS, LKO_RADIUS)
        assert dv == pytest.approx(0.0, abs=1e-6)

    def test_post_launch_circularize(self):
        """Circularizing at apoapsis of a sub-orbital trajectory."""
        # After gravity turn: pe=70km, ap=80km
        r_pe = R_KERBIN + 30_000
        r_ap = R_KERBIN + 80_000
        a = (r_pe + r_ap) / 2
        dv = circularization_delta_v(MU_KERBIN, r_ap, a)
        assert dv > 0  # Need prograde burn


class TestDeorbit:
    def test_deorbit_dv_positive(self):
        """Deorbit from 100km to 30km periapsis."""
        dv = deorbit_delta_v(MU_KERBIN, LKO_100_RADIUS, R_KERBIN + 30_000)
        assert dv > 0

    def test_deorbit_reasonable_magnitude(self):
        """Deorbit from 100km LKO should be small (~50-100 m/s)."""
        dv = deorbit_delta_v(MU_KERBIN, LKO_100_RADIUS, R_KERBIN + 30_000)
        assert 30 < dv < 200


class TestBurnTime:
    def test_basic_burn(self):
        """Simple burn time calculation with Tsiolkovsky."""
        dv = 100.0  # m/s
        thrust = 200_000.0  # 200 kN
        isp = 320.0  # s
        m0 = 10_000.0  # kg

        t = burn_time(dv, thrust, isp, G0, m0)
        assert t > 0
        assert t < 60  # Should be quick for this setup

    def test_zero_thrust_infinite(self):
        t = burn_time(100.0, 0.0, 320.0, G0, 10_000.0)
        assert t == float("inf")

    def test_mass_flow_rate_positive(self):
        mfr = mass_flow_rate(200_000.0, 320.0, G0)
        assert mfr > 0


class TestPhaseAngle:
    def test_same_position(self):
        angle = current_phase_angle(1.0, 1.0)
        assert angle == pytest.approx(0.0, abs=1e-10)

    def test_opposite(self):
        angle = current_phase_angle(0.0, math.pi)
        assert angle == pytest.approx(math.pi, rel=1e-10)

    def test_wraps_positive(self):
        angle = current_phase_angle(math.pi, 0.5)
        assert 0 <= angle < 2 * math.pi


class TestGravityTurnODE:
    def test_vertical_flight(self):
        """At gamma=pi/2 (straight up), cos(gamma)=0 so gravity turn terms vanish."""
        gamma = math.pi / 2
        # dg/dt should be near zero for straight-up flight
        dg = dgamma_dt(v=100.0, r=600_000, gamma=gamma, mu=MU_KERBIN, T=0, m=1000)
        assert abs(dg) < 1e-6

    def test_speed_increases_with_thrust(self):
        """With thrust and gamma=pi/2, dv/dt = T/m - g."""
        T = 50_000
        m = 5_000
        g = 9.81
        gamma = math.pi / 2
        dv = dv_dt(T, m, g, gamma)
        assert dv == pytest.approx(T / m - g, rel=1e-10)

    def test_radial_velocity_vertical(self):
        """At gamma=pi/2, dr/dt = v."""
        v = 200.0
        dr = dr_dt(v, math.pi / 2)
        assert dr == pytest.approx(v, rel=1e-10)

    def test_radial_velocity_horizontal(self):
        """At gamma=0, dr/dt = 0."""
        dr = dr_dt(200.0, 0.0)
        assert dr == pytest.approx(0.0, abs=1e-10)
