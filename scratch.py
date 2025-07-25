import krpc
import os
from dotenv import load_dotenv

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
    # Just wait for autopilot to complete!
    vsl.name = "DUNE-LINK-00"
    print(f"Vessel name: {vsl.name}")


def change_vessel_type():
    conn = krpc.connect(
        name="Pre-Launch Gravity Turn",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )

    vsl = conn.space_center.active_vessel
    body = vsl.orbit.body

    print(f"Vessel type: {vsl.type}")
    vsl.type = vsl.type.probe
    print(f"Vessel type: {vsl.type}")


if __name__ == "__main__":
    # change_vessel_name()
    # change_vessel_type()
    from core.utils.helpers import execute_current_node

    from core.orbital.ht import hohmann_transfer

    hohmann_transfer(target_body_name="Mun")
    execute_current_node()
