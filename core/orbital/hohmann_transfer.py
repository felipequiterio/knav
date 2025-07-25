import math
import os
import krpc
from utils import SpaceLogger

logger = SpaceLogger("HOHMANN_TRANSFER")


def hohmann_transfer(
    target_body_name: str,
):
    """
    Plan the first burn of a Hohmann transfer from the current body to *target_body_name*
    and create a maneuver node.

    Returns:
        tuple: (maneuver_node, transfer_time, dv1, dv2) where:
            - maneuver_node: The created maneuver node for the first burn
            - transfer_time: Time to complete the transfer in seconds
            - dv1: Delta-v required for the first burn (m/s)
            - dv2: Delta-v required for the second burn (m/s)
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

    # ───────── Orbital parameters ─────────
    r1 = vsl.orbit.radius  # [m] current orbital radius
    r2 = target.orbit.semi_major_axis  # [m] target orbit

    logger.status("=== HOHMANN TRANSFER CALCULATION ===")
    logger.status("Orbital parameters:")
    logger.status(f"  • Vessel orbital radius: {r1 / 1000:.1f} km")
    logger.status(f"  • Target orbital radius: {r2 / 1000:.1f} km")
    logger.status(
        f"  • Transfer ellipse semi-major axis: {(r1 + r2) / 2 / 1000:.1f} km"
    )

    # ───────── Delta-v calculation ─────────
    dv1 = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    dv2 = math.sqrt(mu / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))

    # ───────── Transfer time calculation of ellipse ─────────
    transfer_semi_major_axis = (r1 + r2) / 2
    transfer_time = math.pi * math.sqrt(transfer_semi_major_axis**3 / mu)

    # ───────── Phase angle calculation ─────────
    # Get current positions in the central body's non-rotating reference frame
    vessel_position = vsl.position(rf)
    target_position = target.position(rf)

    # Calculate angular positions around central body
    vessel_angle = math.atan2(vessel_position[1], vessel_position[0])
    target_angle = math.atan2(target_position[1], target_position[0])

    # Normalize angles to [0, 2π]
    vessel_angle = vessel_angle % (2 * math.pi)
    target_angle = target_angle % (2 * math.pi)

    # Current phase angle (how far ahead target is from vessel)
    current_phase_angle = (target_angle - vessel_angle) % (2 * math.pi)

    # Angular velocities
    omega_vessel = math.sqrt(mu / r1**3)
    omega_target = math.sqrt(mu / r2**3)

    # For intercept: vessel travels 180° in transfer_time, target travels omega_target * transfer_time
    # At intercept: vessel_angle_start + 180° = target_angle_start + omega_target * transfer_time
    # Therefore: target_angle_start = vessel_angle_start + 180° - omega_target * transfer_time
    # Phase angle needed: target_angle_start - vessel_angle_start = 180° - omega_target * transfer_time
    # BUT: For proper intercept, target should be BEHIND vessel by this amount

    required_phase_angle = (omega_target * transfer_time) - math.pi

    # Normalize to [0, 2π]
    required_phase_angle = required_phase_angle % (2 * math.pi)

    logger.status("Using correct Hohmann intercept formula")
    logger.status(
        f"Required phase angle: {math.degrees(required_phase_angle):.1f}° (target behind vessel)"
    )
    logger.status(
        f"Target should be {math.degrees(math.pi - omega_target * transfer_time):.1f}° behind vessel at launch"
    )

    # Calculate wait time to achieve required phase angle
    # Phase angle changes at rate: omega_target - omega_vessel (relative motion)
    angular_velocity_difference = omega_target - omega_vessel

    if abs(angular_velocity_difference) < 1e-10:
        logger.warning(
            "Vessel and target have same angular velocity - no relative motion"
        )
        wait_time = 0
    else:
        # We want: (target_angle + omega_target * t) - (vessel_angle + omega_vessel * t) = required_phase_angle
        # Rearranging: current_phase_angle + (omega_target - omega_vessel) * t = required_phase_angle
        # Therefore: t = (required_phase_angle - current_phase_angle) / (omega_target - omega_vessel)

        phase_change_needed = required_phase_angle - current_phase_angle

        # Calculate both possible wait times (direct and wrapped around)
        wait_time_1 = phase_change_needed / angular_velocity_difference
        wait_time_2 = (phase_change_needed - 2 * math.pi) / angular_velocity_difference

        # Make both positive
        synodic_period = (2 * math.pi) / abs(angular_velocity_difference)
        while wait_time_1 < 0:
            wait_time_1 += synodic_period
        while wait_time_2 < 0:
            wait_time_2 += synodic_period

        # Always pick the shorter wait time
        wait_time = min(wait_time_1, wait_time_2)

        # Sanity check: reject unreasonably long wait times
        if wait_time > 24 * 3600:  # More than 1 day
            logger.warning(
                f"Wait time very long ({wait_time / 3600:.1f} hours), using modulo"
            )
            wait_time = wait_time % synodic_period

        logger.status(
            f"Choosing shorter wait time: {wait_time / 3600:.2f} hours (vs {max(wait_time_1, wait_time_2) / 3600:.2f} hours)"
        )

    # ───────── Create maneuver node ─────────
    ut = conn.space_center.ut + wait_time

    # Create the maneuver node at the correct time
    maneuver_node = vsl.control.add_node(ut, prograde=dv1)

    # ───────── Calculate positions at launch and arrival ─────────
    # Where will vessel and target be at launch time?
    vessel_angle_at_launch = (vessel_angle + omega_vessel * wait_time) % (2 * math.pi)
    target_angle_at_launch = (target_angle + omega_target * wait_time) % (2 * math.pi)
    phase_angle_at_launch = (target_angle_at_launch - vessel_angle_at_launch) % (
        2 * math.pi
    )

    # Where will they be when transfer completes?
    vessel_angle_at_arrival = (vessel_angle_at_launch + math.pi) % (
        2 * math.pi
    )  # Vessel travels 180°
    target_angle_at_arrival = (
        target_angle_at_launch + omega_target * transfer_time
    ) % (2 * math.pi)

    # Check intercept accuracy
    intercept_error = abs(vessel_angle_at_arrival - target_angle_at_arrival)
    if intercept_error > math.pi:
        intercept_error = 2 * math.pi - intercept_error

    # ───────── Logging results ─────────
    logger.status("=== TRANSFER CALCULATIONS COMPLETE ===")
    logger.status("Phase angle analysis:")
    logger.status(f"  • Current vessel angle: {math.degrees(vessel_angle):.1f}°")
    logger.status(f"  • Current target angle: {math.degrees(target_angle):.1f}°")
    logger.status(f"  • Current phase angle: {math.degrees(current_phase_angle):.1f}°")
    logger.status(
        f"  • Required phase angle: {math.degrees(required_phase_angle):.1f}°"
    )
    logger.status("")
    logger.status("Launch window analysis:")
    logger.status(
        f"  • Vessel angle at launch: {math.degrees(vessel_angle_at_launch):.1f}°"
    )
    logger.status(
        f"  • Target angle at launch: {math.degrees(target_angle_at_launch):.1f}°"
    )
    logger.status(
        f"  • Phase angle at launch: {math.degrees(phase_angle_at_launch):.1f}°"
    )
    logger.status("")
    logger.status("Intercept analysis:")
    logger.status(
        f"  • Vessel angle at arrival: {math.degrees(vessel_angle_at_arrival):.1f}°"
    )
    logger.status(
        f"  • Target angle at arrival: {math.degrees(target_angle_at_arrival):.1f}°"
    )
    logger.status(f"  • Intercept accuracy: {math.degrees(intercept_error):.2f}° error")
    logger.status("")
    logger.status("Transfer parameters:")
    logger.status(f"  • First burn Δv: {dv1:.1f} m/s")
    logger.status(f"  • Second burn Δv: {dv2:.1f} m/s")
    logger.status(f"  • Total Δv: {abs(dv1) + abs(dv2):.1f} m/s")
    logger.status(f"  • Transfer time: {transfer_time / 3600:.2f} hours")
    logger.status(f"  • Wait time: {wait_time / 3600:.2f} hours")
    logger.status(f"  • Burn scheduled at: T+{wait_time:.0f}s")

    logger.info("Maneuver node created successfully!")
    logger.info("Execute the maneuver when the node timer reaches zero.")

    # execute_node(conn, vsl, maneuver_node)
    return maneuver_node, transfer_time, dv1, dv2
