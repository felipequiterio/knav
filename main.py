from core.orbital.circularization import circularization
from utils import SpaceLogger
from core.launch.gravity_turn import gravity_turn, pre_launch

logger = SpaceLogger("KOS")


def main():
    """Main entry point for the KOS system."""

    try:
        logger.mission_start("Gravity Turn")

        logger.status("Starting pre-launch checks...")
        pre_launch()
        logger.status("Pre-launch checks completed!")
        logger.info("Starting gravity turn...")
        gravity_turn(120_000)
        logger.status("Gravity turn completed!")
        logger.mission_complete("Gravity Turn")

        logger.mission_start("Circularization")
        logger.info("Starting circularization...")
        circularization()
        logger.status("Circularization completed!")
        logger.mission_complete("Circularization")

    except Exception as e:
        logger.error(f"Mission failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
