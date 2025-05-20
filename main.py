from core.launch.gravity_turn import gravity_turn
from core.orbital.circularization import circularization
from utils import SpaceLogger

logger = SpaceLogger("KOS")


def main():
    """Main entry point for the KOS system."""
    logger.mission_start("KOS LAUNCH SEQUENCE")

    try:
        logger.info("Starting gravity turn...")
        gravity_turn()
        logger.status("Gravity turn completed!")

        logger.info("Starting circularization...")
        circularization()
        logger.status("Circularization completed!")

        logger.mission_complete("KOS LAUNCH SEQUENCE")
    except Exception as e:
        logger.error(f"Mission failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
