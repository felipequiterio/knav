from core.launch.gravity_turn import pre_launch, gravity_turn
from core.orbital.hohmann_transfer import plan_hohmann_to_body
from core.orbital.circularization import circularization
from utils import SpaceLogger

logger = SpaceLogger("KOS")


def main():
    """Main entry point for the KOS system."""

    try:
        logger.mission_start("Gravity Turn")
        # # change_vessel_name()
        logger.status("Starting pre-launch checks...")
        pre_launch()
        logger.status("Pre-launch checks completed!")
        logger.info("Starting gravity turn...")
        gravity_turn()
        logger.status("Gravity turn completed!")
        logger.mission_complete("Gravity Turn")

        logger.mission_start("Circularization")
        logger.info("Starting circularization...")
        circularization()
        logger.status("Circularization completed!")
        logger.mission_complete("Circularization")

        logger.mission_start("Hohmann Transfer")
        logger.info("Starting Hohmann transfer...")
        plan_hohmann_to_body("Mun")
        logger.status("Hohmann transfer completed!")
        logger.mission_complete("Hohmann Transfer")
    except Exception as e:
        logger.error(f"Mission failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
