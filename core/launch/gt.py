import krpc
import math
import time

from core.utils.formulas import (
    dgamma_dt,
    clamp,
)

from app.app_log import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
GUIDANCE_DT = 0.05  # [s] integration / guidance cycle period
TURN_START_ALT = 1000  # [m] altitude threshold before we start integrating
TARGET_APOAPSIS = 150_000  # [m] desired apoapsis altitude (vacuum)
MAX_Q_RELATIVE = 0.30  # Max-Q as fraction of sea-level static pressure
MIN_TWR = 1.2  # Abort if initial thrust-to-weight ratio below this threshold
MIN_ACCEL = 0.5  # Abort if initial acceleration below this threshold [m/s²]


def gravity_turn(
    conn: krpc.Client,
    target_altitude: int = 150000,
    target_direction: str = "East",
):
    """Launch guidance that steers the vehicle using the planar gravity-turn
    ODE implemented in :pyfunc:`core.utils.formulas.dgamma_dt`.

    Args:
        target_altitude (int): Target apoapsis altitude in meters (default: 150000)
        target_direction (str): Launch direction (default: "East")
    """
    log.info(f"Gravity turn initiated with target altitude: {target_altitude} m.")
    log.info(f"Gravity turn initiated with target direction: {target_direction}.")

    # -- Get vessel and body ----------------------------------------------
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
    def get_heading_from_direction(direction):
        """Convert cardinal direction string to heading in degrees."""
        direction = direction.lower()
        if direction in ["north", "n"]:
            return 0
        elif direction in ["north-east", "ne"]:
            return 45
        elif direction in ["north-west", "nw"]:
            return 135
        elif direction in ["east", "e"]:
            return 90
        elif direction in ["south", "s"]:
            return 180
        elif direction in ["west", "w"]:
            return 270
        else:
            raise ValueError(f"Unknown direction: {direction}")

    # Use the target_direction parameter passed to the function
    heading = get_heading_from_direction(target_direction)
    vsl.control.sas = False
    log.sas("SAS disabled")
    ap = vsl.auto_pilot
    ap.engage()
    log.auto_pilot("Autopilot engaged.")
    log.auto_pilot("Aligning with heading...")
    ap.target_roll = heading  # Roll so that the navball aligns with the heading
    ap.target_pitch_and_heading(90, heading)  # Straight up, specified heading
    log.auto_pilot("Heading aligned.")

    # -- Ignite engines ----------------------------------------------------
    vsl.control.throttle = 1.0

    # -- Release launch clamps --------------------------------------------
    vsl.control.activate_next_stage()
    log.burn("Engines ignited, lift-off...")

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
            log.info("Turn start altitude reached.")
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
        elif APO() < target_altitude * 0.8:
            vsl.control.throttle = 1.0  # full beans while far from Ap
        elif APO() < target_altitude * 0.95:
            vsl.control.throttle = 0.4  # feather as we approach target
        else:
            vsl.control.throttle = 0.1  # creep for fine control

        # Stage if current stage is empty ---------------------------------
        if T == 0:
            log.stage("Staging...")
            vsl.control.activate_next_stage()
            time.sleep(4)
            log.stage("Staging complete.")
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
        ap.target_pitch_and_heading(pitch_cmd, heading)

        log.telemetry(
            {
                "Altitude": f"{ALT():.0f} m",
                "Apoapsis": f"{APO():.0f} m",
                "Pitch": f"{pitch_cmd:.1f}°",
                "Speed": f"{v:.1f} m/s",
                "Gamma": f"{math.degrees(gamma):.1f}°",
                "Thrust": f"{T:.0f} N",
                "Dynamic Pressure": f"{q_dyn / 1000:.1f} kPa",
            }
        )

        # ----- Termination logic: target apoapsis reached ---------------
        if APO() >= target_altitude * 0.98 and q_dyn < 100.0:
            log.status("Approaching target apoapsis - preparing MECO...")
            break

    # --------------------------------------------------------------------
    # Main-engine cut-off (MECO)
    # --------------------------------------------------------------------
    vsl.control.throttle = 0.0
    log.info(f"MECO reached at {ALT() / 1000:.1f} km.")
    log.info(f"Live apoapsis: {APO() / 1000:.1f} km.")
    log.info("Coasting to circularisation...")
