import krpc
import os
import dotenv

dotenv.load_dotenv()


def connect():
    conn = krpc.connect(
        name="Maneuver Buttons",
        address=os.getenv("IP"),
        rpc_port=8077,
        stream_port=8078,
    )
    return conn
