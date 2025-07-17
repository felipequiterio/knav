import krpc
import os
from dotenv import load_dotenv
from core.orbital.hohmann_transfer import plan_hohmann_to_body

load_dotenv()


def change_vessel_name():
    conn = krpc.connect(
        name="Pre-Launch Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )

    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body

    print(f"Vessel name: {vsl.name}")
    vsl.name = "DOBA-SAT-200-01"
    print(f"Vessel name: {vsl.name}")


if __name__ == "__main__":
    # change_vessel_name()
    plan_hohmann_to_body("Mun")
