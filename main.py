from dotenv import load_dotenv
from core.launch.gravity_turn import gravity_turn

load_dotenv()


def main():
    """Main entry point for the KOS system."""
    # try:
    #     conn = krpc.connect(
    #         name="Launch Sequence",
    #         address=os.getenv("IP"),
    #         rpc_port=8075,
    #         stream_port=8076,
    #     )
    #     print("Launch control connected!")
    # except:
    #     print("Failed to connect to launch control")
    #     raise

    print("Starting gravity turn...")
    gravity_turn()
    print("Gravity turn completed!")


if __name__ == "__main__":
    main()
