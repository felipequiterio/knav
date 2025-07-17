from core.launch.L_gravity_turn import gravity_turn
from core.orbital.circularization import circularization
from utils import SpaceLogger

logger = SpaceLogger("KOS")


def launch_and_orbit():
    """Launch and orbit."""

    try:
        logger.mission_start("Starting launch...")
        gravity_turn(2_800_000)
        logger.mission_complete("Launch completed!")

        logger.mission_start("Starting circularization...")
        circularization()
        logger.mission_complete("Circularization completed!")

        logger.mission_complete("KOS LAUNCH SEQUENCE")
    except Exception as e:
        logger.error(f"Mission failed: {str(e)}")
        raise
