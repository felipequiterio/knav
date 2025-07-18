import math
import os
import krpc
from utils import SpaceLogger

logger = SpaceLogger("HOHMANN_TRANSFER")


def hohmann_transfer(
    target_body_name: str,
):
    """
    Planeja a primeira queima de uma transferência Hohmann do corpo atual
    até *target_body_name* e cria um maneuver node.

    Parameters
    ----------
    target_body_name : str
        Nome do corpo celeste de destino
    execute_immediately : bool, optional
        Se True, executa o primeiro nó imediatamente após criá-lo. Default: False
    execute_both_burns : bool, optional
        Se True, executa ambas as queimas automaticamente (partida e chegada). Default: False
        Nota: Se True, execute_immediately é ignorado pois ambas são executadas em sequência.
    """
    # ───────── Conexão ─────────
    conn = krpc.connect(
        name=f"Hohmann transfer → {target_body_name}",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    vsl = conn.space_center.active_vessel
    origin = vsl.orbit.body
    target = conn.space_center.bodies[target_body_name]
    rf = origin.non_rotating_reference_frame
    mu = origin.gravitational_parameter  # [m³ s⁻²]

    # ───────── Raios orbitais ─────────
    r1 = vsl.orbit.radius  # [m] current orbital radius where burn occurs
    r2 = target.orbit.semi_major_axis  # [m] órbita do alvo

    logger.status("Orbital radii:")
    logger.status(f"  • Vessel current radius: {r1 / 1000:.1f} km")
    logger.status(f"  • Target semi-major axis: {r2 / 1000:.1f} km")
    logger.status(
        f"  • Transfer ellipse semi-major axis: {(r1 + r2) / 2 / 1000:.1f} km"
    )

    # ───────── Delta-v da transferência ─────────
    a_t = 0.5 * (r1 + r2)
    dv1 = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1) + 7  # [+5 m/s folga]
    dv2 = math.sqrt(mu / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))  # (informativo)

    # ───────── Fase e tempo de espera ─────────
    th = math.pi * math.sqrt(a_t**3 / mu)  # meio-período
    omega_v = math.sqrt(mu / r1**3)  # angular velocity of vessel
    omega_t = math.sqrt(mu / r2**3)  # angular velocity of target

    # Get position vectors in the orbital plane
    pos_v = vsl.position(rf)
    pos_t = target.position(rf)

    # Calculate angles using atan2 to preserve direction
    angle_vessel = math.atan2(pos_v[1], pos_v[0])  # vessel's angle from x-axis
    angle_target = math.atan2(pos_t[1], pos_t[0])  # target's angle from x-axis

    # Current phase angle (target relative to vessel)
    # Positive means target is ahead of vessel in orbital motion
    phase_now = (angle_target - angle_vessel) % (2 * math.pi)

    # Required phase angle for Hohmann transfer (from wiki: 120° separation)
    # Vessel should be 120° BEHIND target when transfer starts
    required_separation_deg = 120.0  # degrees (from KSP wiki)
    target_behind_angle = math.radians(required_separation_deg)
    phase_req = (2 * math.pi - target_behind_angle) % (2 * math.pi)

    # Calculate phase difference and wait time
    # We want to wait until the phase angle becomes phase_req
    dphase = (phase_req - phase_now) % (2 * math.pi)
    wait_t = dphase / abs(omega_v - omega_t)

    # If omega_v ≈ omega_t (similar orbital periods), use alternative calculation
    if abs(omega_v - omega_t) < 1e-10:
        logger.warning(
            "Vessel and target have very similar orbital periods - using synodic period calculation"
        )
        synodic_period = (
            2 * math.pi / abs(omega_v - omega_t)
            if abs(omega_v - omega_t) > 1e-12
            else float("inf")
        )
        wait_t = (dphase / (2 * math.pi)) * synodic_period

    # ───────── Criando o primeiro node (partida) ─────────
    burn_ut = conn.space_center.ut + wait_t
    node1 = vsl.control.add_node(burn_ut, prograde=dv1)

    # ───────── Validate trajectory ─────────
    predicted_orbit = node1.orbit
    predicted_apoapsis = predicted_orbit.apoapsis_altitude
    predicted_periapsis = predicted_orbit.periapsis_altitude

    # Check if trajectory reaches target's orbital radius
    target_altitude = r2 - origin.equatorial_radius  # Convert radius to altitude
    apoapsis_error = abs(predicted_apoapsis - target_altitude)

    logger.status("Trajectory validation:")
    logger.status(f"  • Predicted apoapsis: {predicted_apoapsis / 1000:.1f} km")
    logger.status(f"  • Target orbit altitude: {target_altitude / 1000:.1f} km")
    logger.status(f"  • Apoapsis error: {apoapsis_error / 1000:.1f} km")

    # Check for encounter using closest approach
    try:
        closest_approach_time = predicted_orbit.time_of_closest_approach(target)
        closest_approach_distance = predicted_orbit.distance_at_closest_approach(target)
        logger.status(
            f"  • Closest approach in: {closest_approach_time / 3600:.1f} hours"
        )
        logger.status(
            f"  • Closest approach distance: {closest_approach_distance / 1000:.1f} km"
        )

        # Check if we have a proper encounter (within target's SOI)
        target_soi = target.sphere_of_influence
        if closest_approach_distance < target_soi:
            logger.status(
                f"  ✅ ENCOUNTER DETECTED! Within {target.name}'s SOI ({target_soi / 1000:.0f} km)"
            )
        else:
            logger.warning(
                f"  ❌ NO ENCOUNTER! Outside {target.name}'s SOI by {(closest_approach_distance - target_soi) / 1000:.0f} km"
            )
    except Exception as e:
        logger.warning(f"  • Could not calculate encounter: {e}")

    # Add debug information
    logger.status("Phase angle calculation:")
    logger.status(f"  • Vessel angle: {math.degrees(angle_vessel):.1f}°")
    logger.status(f"  • Target angle: {math.degrees(angle_target):.1f}°")
    logger.status(f"  • Current phase angle: {math.degrees(phase_now):.1f}°")
    logger.status(f"  • Required phase angle: {math.degrees(phase_req):.1f}°")
    logger.status(
        f"  • Target should be BEHIND vessel by: {required_separation_deg:.1f}° (wiki reference)"
    )
    logger.status(f"  • Phase difference to wait: {math.degrees(dphase):.1f}°")
    logger.status(f"  • Wait time: {wait_t / 3600:.2f} hours")

    result = {
        "departure_node": node1,
        "Δv1": dv1,
        "Δv2": dv2,
        "transfer_time": th,
        "burn_in": wait_t,
        "arrival_burn_ut": burn_ut + th,  # Tempo da segunda queima
        "accuracy_percent": 0,
    }
    # Execute first burn
    # execute_node(conn, vsl, node1)
    # Aguardar tempo de transferência
    logger.status(f"Transfer initiated! Coasting for {th / 3600:.1f} hours...")
    return result
