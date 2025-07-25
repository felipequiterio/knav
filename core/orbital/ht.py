import os
import krpc
import math
from utils import SpaceLogger
from graphs import (
    plot_hohmann_transfer_first_burn,
    plot_hohmann_transfer_second_burn,
)
from core.utils.formulas import get_current_phase_angle

logger = SpaceLogger("HOHMANN_TRANSFER")

# Pre-calculated transfer window and ejection angle data for celestial bodies
TRANSFER_DATA = {
    "Mun": {
        "transfer_window": 65.0,  # degrees
        "ejection_angle": 60.0,  # degrees
    },
    "Moho": {
        "transfer_window": 108.2,  # degrees
        "ejection_angle": 61.3,  # degrees
    },
    "Eve": {
        "transfer_window": -54.1,  # degrees
        "ejection_angle": 25.4,  # degrees
    },
    "Duna": {
        "transfer_window": 44.4,  # degrees
        "ejection_angle": -150.9,  # degrees
    },
    "Dres": {
        "transfer_window": 82.1,  # degrees
        "ejection_angle": -123.1,  # degrees
    },
    "Jool": {
        "transfer_window": 96.6,  # degrees
        "ejection_angle": -114.4,  # degrees
    },
    "Eeloo": {
        "transfer_window": 101.4,  # degrees
        "ejection_angle": -111.8,  # degrees
    },
}

RETURN_DATA = {
    "Moho": {
        "transfer_window": 108.2,  # degrees
        "ejection_angle": 61.3,  # degrees
    },
    "Eve": {
        "transfer_window": -36.1,  # degrees
        "ejection_angle": -162.8,  # degrees
    },
    "Duna": {
        "transfer_window": -75.2,  # degrees
        "ejection_angle": 58.9,  # degrees
    },
    "Dres": {
        "transfer_window": -30.3,  # degrees
        "ejection_angle": 85.0,  # degrees
    },
    "Jool": {
        "transfer_window": 48.7,  # degrees
        "ejection_angle": 19.6,  # degrees
    },
    "Eeloo": {
        "transfer_window": -80.3,  # degrees
        "ejection_angle": 85.0,  # degrees
    },
}


def hohmann_transfer(
    target_body_name: str,
):
    """
    Plan the first burn of a Hohmann transfer from the current body to *target_body_name*
    and create a maneuver node.
    Uses pre-calculated transfer window data when available for optimal timing.
    """
    conn = krpc.connect(
        name=f"Hohmann transfer → {target_body_name}",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    # ----------------- Core parameters -----------------
    vsl = conn.space_center.active_vessel
    origin = vsl.orbit.body
    origin_body = conn.space_center.bodies[origin.name]
    target = conn.space_center.bodies[target_body_name]
    rf = origin.non_rotating_reference_frame

    # ----------------- Orbital parameters -----------------
    r0 = origin_body.orbit.radius  # [m] origin orbit radius
    r1 = vsl.orbit.radius  # [m] current orbital radius
    r2 = target.orbit.radius  # [m] target orbit
    mu = origin.gravitational_parameter  # [m³ s⁻²] gravitational parameter
    vsl_mean_altitude = (vsl.orbit.apoapsis_altitude + vsl.orbit.periapsis_altitude) / 2

    # ----------------- Delta-v calculation -----------------
    # This is the "Hohmann transfer delta-v" formula for the first burn (physics: Hohmann transfer orbit)
    dv1 = math.sqrt(origin.gravitational_parameter / r1) * (
        math.sqrt(2 * r2 / (r1 + r2)) - 1
    )
    # This is the "Hohmann transfer delta-v" formula for the second burn (physics: Hohmann transfer orbit)
    dv2 = math.sqrt(origin.gravitational_parameter / r2) * (
        1 - math.sqrt(2 * r1 / (r1 + r2))
    )

    # ----------------- Transfer time calculation of ellipse -----------------
    transfer_semi_major_axis = (r1 + r2) / 2
    transfer_time = math.sqrt((4 * math.pi**2) / mu * transfer_semi_major_axis**3)

    # ----------------- Current phase angle -----------------
    current_phase = get_current_phase_angle(vsl, origin, target)

    # ----------------- Time to wait until phase match -----------------
    orbital_period_target = 2 * math.pi * math.sqrt(r2**3 / mu)
    angular_velocity_target = 2 * math.pi / orbital_period_target

    phase_diff = (required_phase - current_phase) % (2 * math.pi)
    time_until_burn = phase_diff / angular_velocity_target

    ut_burn = conn.space_center.ut + time_until_burn

    # ----------------- Logging -----------------
    logger.status("=== HOHMANN TRANSFER CALCULATION ===")
    logger.status("Orbital parameters:")
    logger.status(f"  • Vessel name: {vsl.name}")
    logger.status(f"  • Vessel mean altitude: {vsl_mean_altitude / 1000:.1f} km")
    logger.status(f"  • Vessel orbital radius: {r1 / 1000:.1f} km")
    logger.status(f"  • Vessel body: {vsl.orbit.body.name}")
    logger.status(f"  • Target orbital radius: {r2 / 1000:.1f} km")
    logger.status(f"  • Target body: {target.name}")
    logger.status(
        f"  • Current phase angle: {current_phase:.3f} rad ({math.degrees(current_phase):.1f}°)"
    )
    logger.status(
        f"  • Required phase angle: {required_phase:.3f} rad ({math.degrees(required_phase):.1f}°)"
    )

    # Log pre-calculated data if available
    if target_body_name in TRANSFER_DATA:
        logger.status(
            f"  • Transfer window: {TRANSFER_DATA[target_body_name]['transfer_window']:.1f}°"
        )
        logger.status(
            f"  • Ejection angle: {TRANSFER_DATA[target_body_name]['ejection_angle']:.1f}°"
        )

    logger.status("Transfer parameters:")
    logger.status(f"  • Delta-v for first burn: {dv1:.1f} m/s")
    logger.status(f"  • Delta-v for second burn: {dv2:.1f} m/s")
    logger.status(f"  • Transfer time: {transfer_time:.1f} s")
    logger.status(f"  • Transfer time in hours: {transfer_time / 3600:.1f} h")
    logger.status(f"  • Time until optimal burn: {time_until_burn:.1f} s")

    plot_hohmann_transfer_first_burn(
        m_a=vsl_mean_altitude,
        r_1=r1,
        r_2=r2,
        filename="docs/maneuvers/graphs/HOHMANN-TRANSFER-1.png",
    )
    plot_hohmann_transfer_second_burn(
        m_a=vsl_mean_altitude,
        r_1=r1,
        r_2=r2,
        filename="docs/maneuvers/graphs/HOHMANN-TRANSFER-2.png",
    )

    node = vsl.control.add_node(ut_burn, prograde=dv1)
    # from core.utils.helpers import execute_node

    # execute_node(conn, vsl, node)
