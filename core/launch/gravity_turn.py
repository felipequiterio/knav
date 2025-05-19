import math
import time
from dotenv import load_dotenv
import krpc
import os

last_status = 0
load_dotenv()


# –– constants –– --------------------------------------------------
TURN_START_ALT = 250  # [m] altitude where the gravity turn begins
TARGET_APOAPSIS = 100_000  # [m]
DT = 0.05  # [s] guidance cycle period

# –– main –– --------------------------------------------------


def gravity_turn():
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
    ALT = lambda: flt.mean_altitude  # [m] above sea level
    APO = lambda: vsl.orbit.apoapsis_altitude  # [m]
    SPEED = lambda: flt.speed  # [m/s]
    V_VERT = lambda: flt.vertical_speed  # [m/s]
    V_HORIZ = lambda: flt.horizontal_speed  # [m/s]
    DRAG = lambda: flt.drag  # 3‑vector [N]
    MASS = lambda: vsl.mass  # [kg]
    THRUST = lambda: vsl.thrust  # [N]
    ALPHA = lambda: math.radians(flt.angle_of_attack)  # [rad]
    RADIUS = lambda: vsl.orbit.radius  # [m] planet‑center
    G_LOCAL = lambda r: body.gravitational_parameter / r**2  # [m/s²]

    # –– launch config –– --------------------------------------------------
    vsl.control.sas = False
    vsl.auto_pilot.engage()
    vsl.auto_pilot.target_roll = 90  # heads east
    vsl.auto_pilot.target_pitch_and_heading(90, 90)
    vsl.control.throttle = 1.0
    vsl.control.activate_next_stage()  # fire the engines!

    # –– main ascent loop –– ----------------------------------------------
    last_t = conn.space_center.ut
    print("\n" + "=" * 60)
    print(f"Starting main ascent loop at t={last_t:.1f}s")
    print("=" * 60 + "\n")
    print("[STATUS] Waiting to clear tower...")

    while True:
        time.sleep(DT)
        t = conn.space_center.ut
        dt = t - last_t
        last_t = t

        # Skip ODE until we've cleared the tower
        if ALT() < TURN_START_ALT or SPEED() < 1.0:
            # if ALT() < TURN_START_ALT:
            #     print(f"[STATUS] Waiting to clear tower... Alt: {ALT():.1f}m")
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

        if t % 10 < DT:  # Print every ~10 seconds
            print("\n" + "-" * 40)
            print(f"Flight status at T+{t:.1f}s:")
            print("-" * 40)
            print(f"  • Speed:     {v:.1f} m/s")
            print(f"  • Altitude:  {ALT():.1f} m")
            print(f"  • Apoapsis:  {APO():.1f} m")
            print(f"  • Pitch:     {90.0 - math.degrees(gamma):.1f}°")
            print("-" * 40 + "\n")

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

        # ---------- simple ascent termination logic ---------------------
        if APO() > TARGET_APOAPSIS * 0.98:
            print("\n" + "=" * 60)
            print("Approaching target apoapsis")
            print("Final flight status:")
            print("=" * 60)
            print(f"  • Speed:     {v:.1f} m/s")
            print(f"  • Altitude:  {ALT():.1f} m")
            print(f"  • Apoapsis:  {APO():.1f} m")
            print("=" * 60 + "\n")
            break

    # –– cutoff & coast to space –– ---------------------------------------
    vsl.control.throttle = 0.25
    while APO() < TARGET_APOAPSIS:
        time.sleep(0.1)
    vsl.control.throttle = 0.0
    print("\n[STATUS] Target apoapsis reached, coasting to space...")

    while ALT() < 70_500:
        time.sleep(0.2)
    print("[STATUS] Out of atmosphere - prepare for circularisation burn.\n")


# if __name__ == "__main__":
#     conn = krpc.connect(
#         name="Gravity Turn",
#         address=os.getenv("IP"),
#         rpc_port=8075,
#         stream_port=8076,
#     )

#     gravity_turn(conn)
