import os
import krpc
import math
import time

from ..utils import SpaceLogger
from core.utils.formulas import (
    dgamma_dt,
    clamp,
    gravity_local,
    thrust_to_weight,
    acceleration,
)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
GUIDANCE_DT = 0.05  # [s] integration / guidance cycle period
TURN_START_ALT = 250  # [m] altitude threshold before we start integrating
TARGET_APOAPSIS = 150_000  # [m] desired apoapsis altitude (vacuum)
MAX_Q_RELATIVE = 0.30  # Max-Q as fraction of sea-level static pressure
MIN_TWR = 1.2  # Abort if initial thrust-to-weight ratio below this threshold
MIN_ACCEL = 0.5  # Abort if initial acceleration below this threshold [m/s²]

logger = SpaceLogger("GRAVITY_TURN")


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

    # -- mass
    mass = conn.add_stream(getattr, vsl, "mass")  # [kg]

    # -- radius
    radius = conn.add_stream(getattr, vsl.orbit, "radius")  # [m]

    # -- gravitational parameter
    μ = body.gravitational_parameter  # [m³ s⁻²]

    # -- gravity (as a function of current radius)
    grav_local = lambda: gravity_local(μ, radius())  # [m/s²]

    # -- thrust
    available_thrust = conn.add_stream(getattr, vsl, "available_thrust")  # [N]
    thrust_to_weight_ratio = lambda: thrust_to_weight(
        available_thrust(), mass(), grav_local()
    )

    # -- acceleration (computed from thrust and mass as flight.acceleration is unavailable)
    accel = lambda: acceleration(available_thrust(), mass())  # [m/s²]

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

    # -- atmosphere
    has_atmo = body.has_atmosphere
    logger.info(f"Has atmosphere: {has_atmo}")
    atm_top = body.atmosphere_depth if has_atmo else 0  # [m]
    logger.info(f"Atmosphere depth: {atm_top:.2f} m")

    # -- check thrust to weight ratio
    if thrust_to_weight_ratio() < 1.2:
        logger.error("Thrust to weight ratio is too low, aborting")
        return
    logger.info(
        f"Thrust to weight ratio is {thrust_to_weight_ratio():.2f}, continuing..."
    )

    # -- acceletarion
    if accel() < 0.5:
        logger.error("Acceleration is too low, aborting")
        return
    logger.info(f"GO - a₀ = {accel():.2f} m/s²")


def gravity_turn():
    """Launch guidance that steers the vehicle using the planar gravity-turn
    ODE implemented in :pyfunc:`core.utils.formulas.dgamma_dt`.

    """

    logger.mission_start("GRAVITY TURN")

    # -- Establish kRPC connection ----------------------------------------
    conn = krpc.connect(
        name="Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )

    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body
    nrf = body.non_rotating_reference_frame  # Planet-centred inertial-ish
    flt = vsl.flight(nrf)

    # kRPC streams (fast repeated access) ----------------------------------
    ALT = conn.add_stream(getattr, vsl.flight(), "mean_altitude")  # [m]
    APO = conn.add_stream(getattr, vsl.orbit, "apoapsis_altitude")  # [m]
    SPEED = conn.add_stream(getattr, flt, "speed")  # [m/s]
    V_VERT = conn.add_stream(getattr, flt, "vertical_speed")  # [m/s]
    V_HORIZ = conn.add_stream(getattr, flt, "horizontal_speed")  # [m/s]
    RADIUS = conn.add_stream(getattr, vsl.orbit, "radius")  # [m]
    MASS = conn.add_stream(getattr, vsl, "mass")  # [kg]
    THRUST = conn.add_stream(getattr, vsl, "available_thrust")  # [N]
    Q_DYN = conn.add_stream(getattr, vsl.flight(), "dynamic_pressure")  # [Pa]

    # Sea-level static pressure for Max-Q calculation
    p0 = body.pressure_at(0) if body.has_atmosphere else 0.0
    q_limit = MAX_Q_RELATIVE * p0 if body.has_atmosphere else float("inf")

    # Gravitational parameter
    μ = body.gravitational_parameter

    # Fetch instantaneous state --------------------------------------
    v = SPEED()
    v_vert = V_VERT()
    v_horiz = V_HORIZ()
    gamma = math.atan2(v_vert, v_horiz)  # +ve above local horizon [rad]
    r = RADIUS()
    m = MASS()
    T = THRUST()
    q_dyn = Q_DYN()

    # -- Autopilot initialisation ----------------------------------------
    vsl.control.sas = False
    logger.sas("SAS disabled")
    ap = vsl.auto_pilot
    ap.engage()
    logger.auto_pilot("Autopilot engaged")
    ap.target_roll = 90  # Heads east
    ap.target_heading = 90
    ap.target_pitch_and_heading(90, 90)  # Straight up

    # -- Ignite engines ----------------------------------------------------
    vsl.control.throttle = 1.0
    vsl.control.activate_next_stage()
    logger.burn("Engines ignited, lift-off! 🚀")

    last_t = conn.space_center.ut

    # -- Main guidance loop ------------------------------------------------
    while True:
        time.sleep(GUIDANCE_DT)
        t = conn.space_center.ut
        dt = t - last_t
        last_t = t

        # Wait until clear of the tower ----------------------------------
        if ALT() < TURN_START_ALT or SPEED() < 1.0:
            continue
        if ALT() == TURN_START_ALT:
            logger.info("Approaching turn start altitude - preparing to integrate")
            continue

        # Fetch instantaneous state --------------------------------------
        v = SPEED()
        v_vert = V_VERT()
        v_horiz = V_HORIZ()
        gamma = math.atan2(v_vert, v_horiz)  # +ve above local horizon [rad]
        r = RADIUS()
        m = MASS()
        T = THRUST()
        q_dyn = Q_DYN()

        # Throttle management (simple Max-Q and apoapsis guards) ----------
        if q_dyn > q_limit:
            vsl.control.throttle = 0.6  # ease off through Max-Q
        elif APO() < TARGET_APOAPSIS * 0.8:
            vsl.control.throttle = 1.0  # full beans while far from Ap
        elif APO() < TARGET_APOAPSIS * 0.95:
            vsl.control.throttle = 0.4  # feather as we approach target
        else:
            vsl.control.throttle = 0.1  # creep for fine control

        # Stage if current stage is empty ---------------------------------
        if T == 0:
            logger.stage("Staging ...")
            vsl.control.activate_next_stage()
            time.sleep(0.5)
            continue  # Skip guidance update this frame

        # ----------------------------------------------------------------
        # Gravity-turn ODE integration (γ only) ---------------------------
        # ----------------------------------------------------------------
        if v > 0.1 and r > 0.0:  # basic sanity guards
            gamma_dot = dgamma_dt(v, r, gamma, μ, T, m)  # α=L=0
            gamma_next = gamma + gamma_dot * dt
        else:
            gamma_next = gamma  # still essentially vertical

        # Convert desired γ to pitch angle and command the autopilot ------
        pitch_cmd = clamp(90.0 - math.degrees(gamma_next), 0.0, 90.0)
        ap.target_pitch_and_heading(pitch_cmd, 90)

        # Telemetry every ~10 s ------------------------------------------
        if t % 10.0 < GUIDANCE_DT:
            logger.telemetry(
                {
                    "Alt": f"{ALT():.0f} m",
                    "Ap": f"{APO():.0f} m",
                    "Pitch": f"{pitch_cmd:.1f}°",
                    "v": f"{v:.1f} m/s",
                    "γ": f"{math.degrees(gamma):.1f}°",
                    "m": f"{m:.0f} kg",
                    "T": f"{T:.0f} N",
                    "q_dyn": f"{q_dyn / 1000:.1f} kPa",
                }
            )

        # ----- Termination logic: target apoapsis reached ---------------
        if APO() >= TARGET_APOAPSIS * 0.98 and q_dyn < 100.0:
            logger.status("Approaching target apoapsis – preparing MECO")
            break

    # --------------------------------------------------------------------
    # Main-engine cut-off (MECO)
    # --------------------------------------------------------------------
    vsl.control.throttle = 0.0
    logger.info(
        f"MECO at {ALT() / 1000:.1f} km – live Ap {APO() / 1000:.1f} km; coasting "
        "to circularisation."
    )
