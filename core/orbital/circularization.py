# circularization.py
import math
import time
import os
from dotenv import load_dotenv
import krpc
from utils import SpaceLogger

load_dotenv()
logger = SpaceLogger("CIRCULARIZATION")


# –– util –– ---------------------------------------------------------------
def vis_viva(mu: float, r: float, a: float) -> float:
    """Instantaneous orbital velocity (vis-viva equation)."""
    return math.sqrt(mu * (2 / r - 1 / a))


def calculate_burn_time(vessel, delta_v: float) -> float:
    """Burn time estimate using Tsiolkovsky equation."""
    g0 = vessel.orbit.body.surface_gravity
    F = vessel.available_thrust
    Isp = vessel.specific_impulse
    m0 = vessel.mass
    if F <= 0.0:
        logger.error("No thrust available! Are stages activated?")
        raise RuntimeError("No thrust available! Are stages activated?")
    m1 = m0 / math.exp(delta_v / (Isp * g0))
    flow_rate = F / (Isp * g0)  # kg/s
    return (m0 - m1) / flow_rate


# –– main –– ----------------------------------------------------------------
def circularization():
    logger.mission_start("CIRCULARIZATION")
    conn = krpc.connect(
        name="Circularization",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body
    mu = body.gravitational_parameter

    # –– current elliptical orbit parameters ––
    r_a = vsl.orbit.apoapsis
    r_p = vsl.orbit.periapsis
    a = 0.5 * (r_a + r_p)

    # Log initial orbital parameters
    initial_telemetry = {
        "Apoapsis": f"{r_a:,.0f} m",
        "Periapsis": f"{r_p:,.0f} m",
        "Semi-major axis": f"{a:,.0f} m",
        "Eccentricity": f"{vsl.orbit.eccentricity:.4f}",
        "Orbital period": f"{vsl.orbit.period / 60:.1f} min",
    }
    logger.telemetry(initial_telemetry)

    # Step 1: Raise periapsis at apoapsis
    v_a = vis_viva(mu, r_a, a)
    v_circ = math.sqrt(mu / r_a)
    delta_v1 = v_circ - v_a

    # Create first maneuver node at apoapsis
    ut_apo = conn.space_center.ut + vsl.orbit.time_to_apoapsis
    node1 = vsl.control.add_node(ut_apo, prograde=delta_v1)
    logger.status(f"First maneuver node created at UT={ut_apo:.1f}")

    # Estimate burn time
    dt_burn1 = calculate_burn_time(vsl, delta_v1)
    logger.status(f"Estimated burn time: {dt_burn1:.1f}s")

    # Warp to T- (Δt/2)
    warp_to = node1.ut - dt_burn1 / 2 - 5  # 5 s margin
    logger.warp(f"Warping to T-{dt_burn1 / 2:.1f}s (UT={warp_to:.1f})")
    conn.space_center.warp_to(warp_to)

    # Execute first burn
    vsl.auto_pilot.reference_frame = node1.reference_frame
    logger.status("Aligning with first node direction")
    direction = node1.direction(node1.reference_frame)
    vsl.auto_pilot.target_direction = direction
    vsl.auto_pilot.engage()
    vsl.control.sas = True
    vsl.auto_pilot.wait()
    logger.status("Vessel aligned with first maneuver node")

    remaining = conn.add_stream(getattr, node1, "remaining_delta_v")
    logger.burn("First circularization burn initiated")
    vsl.control.throttle = 1.0

    while remaining() > 10.0:
        time.sleep(0.05)

    vsl.control.throttle = 0.0
    time.sleep(0.5)
    node1.remove()

    # Step 2: Lower apoapsis at periapsis
    r_a_new = vsl.orbit.apoapsis
    r_p_new = vsl.orbit.periapsis
    a_new = 0.5 * (r_a_new + r_p_new)

    v_p = vis_viva(mu, r_p_new, a_new)
    v_circ2 = math.sqrt(mu / r_p_new)
    delta_v2 = v_circ2 - v_p

    if abs(delta_v2) < 1.0:  # Less than 1 m/s needed
        logger.status("Orbit is sufficiently circular after first burn")
        return

    # Create second maneuver node at periapsis
    ut_peri = conn.space_center.ut + vsl.orbit.time_to_periapsis
    node2 = vsl.control.add_node(ut_peri, prograde=delta_v2)
    logger.status(f"Second maneuver node created at UT={ut_peri:.1f}")

    # Estimate burn time
    dt_burn2 = calculate_burn_time(vsl, abs(delta_v2))
    logger.status(f"Estimated burn time: {dt_burn2:.1f}s")

    # Warp to T- (Δt/2)
    warp_to = node2.ut - dt_burn2 / 2 - 5
    logger.warp(f"Warping to T-{dt_burn2 / 2:.1f}s (UT={warp_to:.1f})")
    conn.space_center.warp_to(warp_to)

    # Execute second burn
    vsl.auto_pilot.reference_frame = node2.reference_frame
    logger.status("Aligning with second node direction")
    direction = node2.direction(node2.reference_frame)
    vsl.auto_pilot.target_direction = direction
    vsl.auto_pilot.engage()
    vsl.control.sas = True
    vsl.auto_pilot.wait()
    logger.status("Vessel aligned with second maneuver node")

    remaining = conn.add_stream(getattr, node2, "remaining_delta_v")
    logger.burn("Second circularization burn initiated")
    vsl.control.throttle = 1.0

    while remaining() > 10.0:
        time.sleep(0.05)

    vsl.control.throttle = 0.0
    time.sleep(0.5)
    node2.remove()

    # Log final orbit parameters
    final_telemetry = {
        "Final Periapsis": f"{vsl.orbit.periapsis_altitude:,.0f} m",
        "Final Apoapsis": f"{vsl.orbit.apoapsis_altitude:,.0f} m",
        "Difference": f"{abs(vsl.orbit.periapsis_altitude - vsl.orbit.apoapsis_altitude):,.0f} m",
        "Final Eccentricity": f"{vsl.orbit.eccentricity:.4f}",
        "Orbital Period": f"{vsl.orbit.period / 60:.1f} min",
    }
    logger.telemetry(final_telemetry)

    logger.mission_complete("CIRCULARIZATION")
    logger.status("Circular orbit achieved. Mission nominal!")
