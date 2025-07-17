"""Hohmann transfer planning tools."""

import os

import krpc
from dotenv import load_dotenv

from core.utils.formulas import (
    delta_v_hohmann,
    calculate_burn_time,
    calculate_transfer_time,
)
from utils import SpaceLogger

load_dotenv()

logger = SpaceLogger("HOHMANN")


def plan_hohmann_to_body(target_body_name: str, node_lead_time: float = 60.0):
    """Compute a Hohmann transfer from the active vessel to a given body.

    The function:
    1. Connects to kRPC and obtains the active vessel & celestial data.
    2. Computes ∆v requirements for the transfer (central body = vessel.orbit.body).
    3. Logs a detailed summary and, if possible, places the first maneuver node at the correct phase angle.

    Parameters
    ----------
    target_body_name : str
        e.g. "Mun", "Minmus", "Duna" … Must be a child of the current central body.
    node_lead_time : float, optional
        Time (seconds) before the transfer window to position the maneuver node.
        Set to `None` to skip node creation.
    """

    import math

    # ------------------------------------------------------------------ Connect
    conn = krpc.connect(
        name=f"Hohmann transfer → {target_body_name}",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )

    vsl = conn.space_center.active_vessel
    origin_body = vsl.orbit.body

    # ------------------------------------------------------------- Target body
    try:
        target_body = conn.space_center.bodies[target_body_name]
    except KeyError as exc:
        logger.error(f"Celestial body '{target_body_name}' not found. Check spelling.")
        raise exc

    # ------------------------------------------------------- Orbit parameters
    mu = origin_body.gravitational_parameter

    # Current orbit – assume near-circular (use semi-major axis for robustness)
    r1 = vsl.orbit.semi_major_axis

    # Target orbit radius – use semi-major axis of body's orbit around parent
    r2 = target_body.orbit.semi_major_axis

    dv1, dv2 = delta_v_hohmann(mu, r1, r2)
    dv1 = dv1 * 1.05  # Add 5% margin

    # ------------------------------------------------------------- Telemetry
    summary = {
        "Central body": origin_body.name,
        "Target body": target_body.name,
        "r₁ (start)": f"{r1:,.0f} m",
        "r₂ (target)": f"{r2:,.0f} m",
        "∆v₁": f"{dv1:+.1f} m/s",
        "∆v₂": f"{dv2:+.1f} m/s",
        "Total ∆v": f"{abs(dv1) + abs(dv2):.1f} m/s",
    }

    logger.telemetry(summary)

    # Calculate transfer time
    transfer_time = calculate_transfer_time(mu, r1, r2)
    # Target orbital period
    target_period = 2 * math.pi * math.sqrt(r2**3 / mu)
    # Required phase angle in degrees
    phase_angle = 180 - (transfer_time / target_period) * 360

    logger.status(f"Required phase angle for transfer: {phase_angle:.2f}°")

    # Get current phase angle (angle from vessel to target, measured prograde from vessel's position)
    # Compute positions in the parent body's reference frame
    vessel_true_anomaly = vsl.orbit.true_anomaly
    target_true_anomaly = target_body.orbit.true_anomaly

    # Both true anomalies are in radians, but we want the angle from vessel to target, measured prograde
    # The phase angle is the angle from the vessel to the target, measured in the direction of the orbit
    # (i.e., target's mean anomaly minus vessel's mean anomaly, normalized to [0, 360))
    vessel_mean_anomaly = vsl.orbit.mean_anomaly
    target_mean_anomaly = target_body.orbit.mean_anomaly

    # Convert mean anomaly to degrees
    vessel_deg = math.degrees(vessel_mean_anomaly) % 360
    target_deg = math.degrees(target_mean_anomaly) % 360

    current_phase_angle = (target_deg - vessel_deg) % 360

    logger.status(f"Current phase angle: {current_phase_angle:.2f}°")

    # Calculate time to correct phase angle
    # The phase angle increases at the rate of the difference in mean motions
    # mean motion n = 2π / period
    vessel_period = 2 * math.pi * math.sqrt(r1**3 / mu)
    vessel_n = 2 * math.pi / vessel_period
    target_n = 2 * math.pi / target_period

    # Phase angle rate (deg/s)
    phase_rate = (target_n - vessel_n) * 180 / math.pi  # deg/s

    # Determine the phase difference so that the resulting time is **positive**
    if phase_rate >= 0:
        delta_phase = (phase_angle - current_phase_angle) % 360
    else:
        delta_phase = (current_phase_angle - phase_angle) % 360

    if abs(phase_rate) < 1e-6:
        logger.warning(
            "Phase rate is too small; orbits may be identical or calculation failed."
        )
        time_to_transfer = 0
    else:
        time_to_transfer = delta_phase / abs(phase_rate)

    # Ensure the node is not created too close to the present (\u003c 30 s)
    # If it is, wait one additional synodic period.
    if time_to_transfer < 30:
        synodic_period = 360 / abs(phase_rate)  # time for a full phase cycle
        time_to_transfer += synodic_period

    logger.status(
        f"Time until transfer window: {time_to_transfer:.1f} s ({time_to_transfer / 60:.1f} min)"
    )

    # ---------------------------------------------------------------- Burn-time estimate (used to center the node)
    Isp = vsl.specific_impulse  # [s]
    body = vsl.orbit.body
    g0 = body.surface_gravity  # [m/s^2]
    m0 = vsl.mass  # [kg]
    m_dot = vsl.available_thrust / (Isp * g0)  # [kg/s]

    try:
        burn_est = calculate_burn_time(m_dot, m0, abs(dv1), Isp, g0)
    except RuntimeError as err:
        logger.warning(str(err))
        burn_est = 0.0

    # ---------------------------------------------------------------- Warp and node timing
    # We want the *mid-point* of the burn to happen exactly at the computed transfer time.
    # Therefore the node time (which is the burn mid-point) is:
    ut_now = conn.space_center.ut
    node_ut_center = ut_now + time_to_transfer + burn_est / 2.0

    # We will warp so that the vessel is oriented "node_lead_time" seconds BEFORE the *start* of the burn.
    node_ut_start = node_ut_center - burn_est / 2.0
    warp_target = node_ut_start - node_lead_time

    if warp_target < ut_now:
        logger.warning(
            "Transfer window is too close or in the past. Creating node immediately."
        )
        warp_target = ut_now + 5  # Give a 5-second margin

    lead_txt = f"T-{(node_ut_start - warp_target):.0f}s before burn"
    logger.warp(f"Warping to UT={warp_target:.1f} for transfer window ({lead_txt})")
    conn.space_center.warp_to(warp_target)

    # ---------------------------------------------------------------- Create the maneuver node
    node = vsl.control.add_node(node_ut_center, prograde=dv1)
    logger.maneuver(
        f"Maneuver node created at UT={node.ut:.1f} (burn starts in {node_ut_start - conn.space_center.ut:.0f}s) "
        f"with prograde ∆v={dv1:+.1f} m/s"
    )

    logger.status(f"Estimated burn time: {burn_est:.1f} s")

    return dv1, dv2
