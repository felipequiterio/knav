import krpc
import os
from dotenv import load_dotenv
from ..utils import SpaceLogger
import math
import time
from core.parts.part_control import (
    deploy_fairing,
    control_solar_panel,
    control_antenna,
)

logger = SpaceLogger("Pre-Launch Gravity Turn")

load_dotenv()


def pre_launch():
    """
    Pre-launch setup for the gravity turn.
    """
    conn = krpc.connect(
        name="Pre-Launch Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )

    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body

    # get_part_info(vsl, "G-01 Fairing Half")
    # –– reference frames –– ----------------------------------------------
    nrf = body.non_rotating_reference_frame  # inertial‑ish

    # -- altitude
    radius = conn.add_stream(getattr, vsl.orbit, "radius")  # [m]

    # -- mass
    mass = conn.add_stream(getattr, vsl, "mass")  # [kg]

    # -- radius
    radius = conn.add_stream(getattr, vsl.orbit, "radius")  # [m]

    # -- gravity (as a function of current radius)
    gravity_local = lambda: body.gravitational_parameter / (radius() ** 2)  # [m/s²]

    # -- thrust
    available_thrust = conn.add_stream(getattr, vsl, "available_thrust")  # [N]
    thrust_to_weight = lambda: available_thrust() / (
        mass() * gravity_local()
    )  # [dimensionless]

    # -- acceleration (computed from thrust and mass as flight.acceleration is unavailable)
    acceleration = lambda: available_thrust() / mass()  # [m/s²]

    # -- activate next stage
    vsl.control.throttle = 1.0
    vsl.control.activate_next_stage()

    # --------------------------- START PRE-LAUNCH CHECKS ---------------------------

    # -- body
    body = vsl.orbit.body
    body_name = body.name
    logger.info(f"Body: {body_name}")

    # -- gravitational parameter
    μ = body.gravitational_parameter  # [m³ s⁻²]
    logger.info(f"Gravitational parameter: {μ:.2f} m³ s⁻²")

    # -- equatorial radius
    R = body.equatorial_radius  # [m]
    logger.info(f"Equatorial radius: {R:.2f} m")

    # -- surface gravity
    g0 = μ / R**2  # surface g  [m s⁻²]
    logger.info(f"Surface gravity: {g0:.2f} m s⁻²")

    # -- rotational period
    Ω = 2 * math.pi / body.rotational_period  # [rad s⁻¹]
    logger.info(f"Rotational period: {Ω:.2f} rad s⁻¹")

    # -- atmosphere
    has_atmo = body.has_atmosphere
    logger.info(f"Has atmosphere: {has_atmo}")
    atm_top = body.atmosphere_depth if has_atmo else 0  # [m]
    logger.info(f"Atmosphere depth: {atm_top:.2f} m")

    # -- check thrust to weight ratio
    if thrust_to_weight() < 1.2:
        logger.error("Thrust to weight ratio is too low, aborting")
        return
    logger.info(f"Thrust to weight ratio is {thrust_to_weight():.2f}, continuing...")

    # -- acceletarion
    if acceleration() < 0.5:
        logger.error("Acceleration is too low, aborting")
        return
    logger.info(f"GO - a₀ = {acceleration():.2f} m/s²")


def gravity_turn(orbit_target=120_000, safety_margin_km=5):
    """
    One-function gravity-turn that compensates for in-atmosphere drag
    by (i) waiting for thin air *and* (ii) aiming a bit high.

    Parameters
    ----------
    orbit_target : float
        Desired *final* apoapsis altitude [m] **after** drag-settling.
    safety_margin_km : float
        Extra km to build into the live apoapsis while still in air.
    """

    # --------------- connection / handles ----------------------------------
    conn = krpc.connect(
        name="Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body

    # --------------- atmosphere metadata -----------------------------------
    has_atmo = body.has_atmosphere
    atm_top = body.atmosphere_depth if has_atmo else 0.0  # [m]

    # --------------- dynamic streams ---------------------------------------
    alt = conn.add_stream(getattr, vsl.flight(), "mean_altitude")
    apo = conn.add_stream(getattr, vsl.orbit, "apoapsis_altitude")
    q_dyn = conn.add_stream(getattr, vsl.flight(), "dynamic_pressure")
    thrust = conn.add_stream(getattr, vsl, "thrust")  # [N]

    # --------------- pitch profile (unchanged) -----------------------------
    h_s = 500 if not has_atmo else max(200, 0.02 * atm_top)
    h_e = 0.4 * orbit_target if not has_atmo else 0.65 * atm_top
    k = 1.5

    # --------------- max-Q limit -------------------------------------------
    p0 = body.pressure_at(0) if has_atmo else 0.0
    q_limit = 0.3 * p0 if has_atmo else float("inf")

    # --------------- autopilot ---------------------------------------------
    ap = vsl.auto_pilot
    ap.engage()
    ap.target_heading = 90
    ap.target_roll = 0

    approach_band = orbit_target + 5_000
    final_band = orbit_target + 1_000

    # --------------- helper: cutoff criterion ------------------------------
    def safe_to_cut():
        """
        True when (a) live apoapsis high enough AND (b) ship is above ~95 % of
        the atmosphere or q_dyn ~ 0.  Works for airless worlds too.
        """
        high_enough = apo() >= orbit_target
        thin_air = (alt() >= 0.95 * atm_top) if has_atmo else True
        negligible_q = q_dyn() < 100.0  # ≈0.1 kPa
        return high_enough and (thin_air or negligible_q)

    # --------------- helper: stage fuel ------------------------------------

    logger.info(f"Resouce names: {vsl.resources.names}")
    logger.info(f"Liquid Hydrogen: {vsl.resources.amount('LqdHydrogen')}")
    # --------------- main loop ---------------------------------------------
    logger.status("Gravity-turn ascent begins")
    vsl.control.throttle = 1.0
    vsl.control.activate_next_stage()

    while True:
        h = alt()

        # ---- pitch S-curve -------------------------------------------------
        if h < h_s:
            pitch = 90
        elif h > h_e:
            pitch = 0
        else:
            F = (h - h_s) / (h_e - h_s)
            pitch = 90 * (1 - F**k)
        ap.target_pitch = pitch

        # ---- throttle ------------------------------------------------------
        if q_dyn() > q_limit:  # Max-Q guard
            vsl.control.throttle = 0.6
        elif apo() < approach_band:  # still far → full
            vsl.control.throttle = 1.0
        elif apo() < final_band:  # feather
            vsl.control.throttle = 0.3
        else:  # creep
            vsl.control.throttle = 0.1

        # ---- stage depletion ------------------------------------------------
        t = thrust()
        if t == 0:  # No thrust means we need to check if we should stage
            logger.stage("Activating next stage...")
            vsl.control.activate_next_stage()
            time.sleep(3)  # Give time for stage activation
            continue

        # ---- cut-off logic -------------------------------------------------
        apo_target_live = (
            orbit_target + safety_margin_km * 1000
            if h < 0.95 * atm_top
            else orbit_target
        )
        if apo() >= apo_target_live and safe_to_cut():
            break

        time.sleep(0.05)

    # --------------- engine cut-off ----------------------------------------
    vsl.control.throttle = 0.0
    deploy_fairing(vsl, "G-01 Fairing Half")
    time.sleep(1)
    control_solar_panel(vsl, "SP-002 1x6 Photovoltaic Panels")
    control_antenna(vsl, "C3 Communotron DTS-M1", "activate")
    logger.info(
        f"MECO at {alt() / 1000:.1f} km, live Ap {apo() / 1000:.1f} km "
        "– coasting to circularise."
    )
