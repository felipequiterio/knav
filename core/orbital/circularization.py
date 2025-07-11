# circularization.py
import math
import time
import os
from dotenv import load_dotenv
import krpc
from utils import SpaceLogger
from core.parts.part_control import control_sas

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

    # Step 1: Raise periapsis at apoapsis
    v_a = vis_viva(mu, r_a, a)
    v_circ = math.sqrt(mu / r_a)
    delta_v1 = v_circ - v_a

    # Create first maneuver node at apoapsis
    ut_apo = conn.space_center.ut + vsl.orbit.time_to_apoapsis
    node1 = vsl.control.add_node(ut_apo, prograde=delta_v1)
    logger.maneuver(f"First maneuver node created at UT={ut_apo:.1f}")

    # Estimate burn time
    dt_burn1 = calculate_burn_time(vsl, delta_v1)
    logger.status(f"Estimated burn time: {dt_burn1:.1f}s")

    # Warp to T- (Δt/2)
    warp_to = node1.ut - dt_burn1 / 2 - 5  # 5 s margin
    logger.warp(f"Warping to T-{dt_burn1 / 2:.1f}s (UT={warp_to:.1f})")
    conn.space_center.warp_to(warp_to)

    vsl.auto_pilot.reference_frame = node1.reference_frame
    logger.align("Aligning with first node direction")
    direction = node1.direction(node1.reference_frame)

    burn_start_ut = conn.space_center.ut
    burn_end_ut = burn_start_ut + dt_burn1

    vsl.auto_pilot.disengage()

    # Enable SAS and ensure it switches to “maneuver-hold”.
    control_sas(vsl, "maneuver")
    logger.align(f"SAS mode confirmed: {vsl.control.sas_mode}")

    # Execute first burn
    logger.burn("First circularization burn initiated")
    # Use remaining ΔV to drive cut-off for higher accuracy
    remaining1 = conn.add_stream(getattr, node1, "remaining_delta_v")

    # Main portion of the burn
    vsl.control.throttle = 1.0
    while remaining1() > 5.0:
        time.sleep(0.05)

    # Feather throttle for the last few m/s to avoid overshoot
    vsl.control.throttle = 0.05
    while remaining1() > 1.0:
        time.sleep(0.05)

    # Ensure throttle is fully closed before proceeding
    vsl.control.throttle = 0.0
    # After burn, switch to stability assist and allow SAS to disengage cleanly
    vsl.control.sas = False
    vsl.control.sas_mode = vsl.control.sas_mode.stability_assist
    time.sleep(0.5)

    # Final pause to let physics settle before node removal
    time.sleep(0.5)

    # ── ΔV audit ──
    dv_predicted = delta_v1  # m/s, based on maneuver computation
    dv_remaining = remaining1()  # m/s left unperformed
    dv_actual = dv_predicted - dv_remaining
    logger.status(
        "ΔV audit (burn-1): predicted {:.1f} m/s | actual {:.1f} m/s | residual {:.2f} m/s".format(
            dv_predicted, dv_actual, dv_remaining
        )
    )

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
    logger.maneuver(f"Second maneuver node created at UT={ut_peri:.1f}")

    # Estimate burn time
    dt_burn2 = calculate_burn_time(vsl, abs(delta_v2))
    logger.status(f"Estimated burn time: {dt_burn2:.1f}s")

    # Warp to T- (Δt/2)
    warp_to = node2.ut - dt_burn2 / 2 - 5
    logger.warp(f"Warping to T-{dt_burn2 / 2:.1f}s (UT={warp_to:.1f})")
    conn.space_center.warp_to(warp_to)

    # Execute second burn
    vsl.auto_pilot.reference_frame = node2.reference_frame
    logger.align("Aligning with second node direction via SAS")

    # Disengage any active autopilot and use SAS maneuver mode (same trick as first burn)
    vsl.auto_pilot.disengage()

    # vsl.control.sas = True
    # for _ in range(5):
    #     vsl.control.sas_mode = SASMode.maneuver
    #     time.sleep(0.1)
    #     if vsl.control.sas_mode == SASMode.maneuver:
    #         break

    control_sas(vsl, "maneuver")
    logger.align(f"SAS mode confirmed: {vsl.control.sas_mode}")
    # Give SAS a moment to settle on the node direction
    time.sleep(2)

    remaining = conn.add_stream(getattr, node2, "remaining_delta_v")
    logger.burn("Second circularization burn initiated")
    vsl.control.throttle = 1.0

    # Burn until only a few m/s remain
    while remaining() > 5.0:
        time.sleep(0.05)

    # Feather throttle for precision
    vsl.control.throttle = 0.05
    while remaining() > 1.0:
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
