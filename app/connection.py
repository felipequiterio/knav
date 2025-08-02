import krpc
import os
from dotenv import load_dotenv

load_dotenv()


def connect_maneuver() -> krpc.Client:
    return krpc.connect(
        name="Maneuver Connection",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )


def connect_telemetry() -> krpc.Client:
    return krpc.connect(
        name="Telemetry Connection",
        address=os.getenv("IP"),
        rpc_port=8077,
        stream_port=8078,
    )
