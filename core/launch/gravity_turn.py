import math
import time
from dotenv import load_dotenv
import krpc
import os
from utils import SpaceLogger

last_status = 0
load_dotenv()
logger = SpaceLogger("GRAVITY_TURN")


# –– constants –– --------------------------------------------------
TURN_START_ALT = 250  # [m] altitude where the gravity turn begins
TARGET_APOAPSIS = 100_000  # [m]
DT = 0.05  # [s] guidance cycle period


# –– main –– --------------------------------------------------
def gravity_turn():
    logger.mission_start("GRAVITY TURN")
    conn = krpc.connect(
        name="Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body

    # –– reference frames –– ----------------------------------------------
    nrf = body.non_rotating_reference_frame  # inertial‑ish
    flt = vsl.flight(nrf)

    # –– helper lambdas (wrapped in streams would be faster) –– ------------
    ALT = conn.add_stream(getattr, vsl.flight(), "mean_altitude")  # [m]
    APO = conn.add_stream(getattr, vsl.orbit, "apoapsis_altitude")  # [m]
    SPEED = conn.add_stream(getattr, flt, "speed")  # [m/s]
    V_VERT = conn.add_stream(getattr, flt, "vertical_speed")  # [m/s]
    V_HORIZ = conn.add_stream(getattr, flt, "horizontal_speed")  # [m/s]
    DRAG = conn.add_stream(getattr, flt, "drag")  # 3‑vector [N]
    MASS = conn.add_stream(getattr, vsl, "mass")  # [kg]
    THRUST = conn.add_stream(getattr, vsl, "thrust")  # [N]
    ALPHA = conn.add_stream(getattr, flt, "angle_of_attack")  # [rad]
    RADIUS = conn.add_stream(getattr, vsl.orbit, "radius")  # [m] planet‑center
    G_LOCAL = lambda r: body.gravitational_parameter / r**2  # [m/s²]

    # Add fuel monitoring streams
    LIQUID_FUEL = conn.add_stream(vsl.resources.amount, "LiquidFuel")
    OXIDIZER = conn.add_stream(vsl.resources.amount, "Oxidizer")
    SOLID_FUEL = conn.add_stream(vsl.resources.amount, "SolidFuel")

    # Log initial launch parameters
    initial_telemetry = {
        "Target Apoapsis": f"{TARGET_APOAPSIS:,.0f} m",
        "Turn Start Altitude": f"{TURN_START_ALT:,.0f} m",
        "Initial Mass": f"{MASS():,.0f} kg",
        "Initial Thrust": f"{THRUST():,.0f} N",
        "Local Gravity": f"{G_LOCAL(RADIUS()):.2f} m/s²",
    }
    logger.info("Launch Parameters:")
    logger.telemetry(initial_telemetry)

    # –– launch config –– --------------------------------------------------
    vsl.control.sas = False
    vsl.auto_pilot.engage()
    vsl.auto_pilot.target_roll = 90  # heads east
    vsl.auto_pilot.target_pitch_and_heading(90, 90)
    vsl.control.throttle = 1.0
    vsl.control.activate_next_stage()  # fire the engines!
    logger.burn("Launch initiated!")

    # –– main ascent loop –– ----------------------------------------------
    last_t = conn.space_center.ut
    logger.status("Starting main ascent loop")
    logger.status("Waiting to clear tower...")

    while True:
        time.sleep(DT)
        t = conn.space_center.ut
        dt = t - last_t
        last_t = t

        # Skip ODE until we've cleared the tower
        if ALT() < TURN_START_ALT or SPEED() < 1.0:
            continue

        # ----------- gather instantaneous state --------------------------
        v = SPEED()
        v_vert = V_VERT()
        v_horiz = V_HORIZ()
        gamma = math.atan2(v_vert, v_horiz)  # [rad]
        m = MASS()
        T = THRUST()
        D_mag = math.sqrt(sum(c * c for c in DRAG()))
        alpha = ALPHA()
        g = G_LOCAL(RADIUS())

        # Check fuel levels and stage if needed
        if T == 0:  # No thrust means we need to check if we should stage
            logger.stage("Activating next stage...")
            vsl.control.activate_next_stage()
            time.sleep(0.5)  # Give time for stage activation
            continue

        if t % 10 < DT:  # Print every ~10 seconds
            flight_telemetry = {
                "Speed": f"{v:.1f} m/s",
                "Altitude": f"{ALT():.1f} m",
                "Apoapsis": f"{APO():.1f} m",
                "Pitch": f"{90.0 - math.degrees(gamma):.1f}°",
                "Mass": f"{m:.0f} kg",
                "Thrust": f"{T:.0f} N",
                "Drag": f"{D_mag:.0f} N",
                "Liquid Fuel": f"{LIQUID_FUEL():.1f}",
                "Oxidizer": f"{OXIDIZER():.1f}",
                "Solid Fuel": f"{SOLID_FUEL():.1f}",
            }
            logger.telemetry(flight_telemetry)

        # ---------- integrate gravity‑turn ODE ---------------------------
        if v > 0.1:  # avoid div‑by‑zero
            dgamma_dt = (-g * math.cos(gamma) / v) + ((T - D_mag) / (m * v)) * math.sin(
                alpha
            )
            gamma_next = gamma + dgamma_dt * dt
        else:
            gamma_next = gamma  # still almost vertical

        # ---------- convert desired γ→pitch, command autopilot ----------
        pitch_cmd = max(0.0, min(90.0, 90.0 - math.degrees(gamma_next)))
        vsl.auto_pilot.target_pitch_and_heading(pitch_cmd, 90)

        # ---------- ascent termination logic ---------------------
        if APO() > TARGET_APOAPSIS * 0.98:
            logger.status("Approaching target apoapsis")

            final_telemetry = {
                "Final Speed": f"{v:.1f} m/s",
                "Final Altitude": f"{ALT():.1f} m",
                "Final Apoapsis": f"{APO():.1f} m",
                "Final Pitch": f"{pitch_cmd:.1f}°",
                "Remaining Mass": f"{m:.0f} kg",
                "Time to Apoapsis": f"{vsl.orbit.time_to_apoapsis / 60:.1f} min",
            }
            logger.telemetry(final_telemetry)
            break

    # –– cutoff & coast to space –– ---------------------------------------
    vsl.control.throttle = 0.25
    while APO() < TARGET_APOAPSIS:
        time.sleep(0.1)
    vsl.control.throttle = 0.0
    logger.status("Target apoapsis reached, coasting to space...")

    while ALT() < 70_500:
        time.sleep(0.2)
    logger.status("Out of atmosphere - prepare for circularisation burn.")

    logger.fairing("Jettisoning fairings...")
    for part in vsl.parts.all:
        if part.title == "Mothra Aerodynamic Fairing":
            for module in part.modules:
                if module.name == "ModuleDecouple":
                    module.trigger_event("Decouple")
        if part.title == "G-01 Fairing Half":
            for module in part.modules:
                if module.name == "ModuleDecouple":
                    module.trigger_event("Decouple")
    logger.mission_complete("GRAVITY TURN")


# if __name__ == "__main__":
#     conn = krpc.connect(
#         name="Gravity Turn",
#         address=os.getenv("IP"),
#         rpc_port=8075,
#         stream_port=8076,
#     )

#     gravity_turn(conn)
