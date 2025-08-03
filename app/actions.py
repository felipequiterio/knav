from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from core.launch.gt import gravity_turn
from core.orbital.circularization import circularization
from core.orbital.hohmann_transfer import hohmann_transfer_to_target
from app.app_log import get_logger
from app.connection import connect_maneuver

log = get_logger(__name__)

conn = connect_maneuver()


def execute_gravity_turn(apoapsis: int, direction: str) -> None:
    """Single-call gravity-turn followed by on-orbit circularisation."""

    gravity_turn(conn, target_altitude=apoapsis * 1000, target_direction=direction)
    circularization()


def action_gravity_turn(console: Console) -> None:
    console.rule("[primary]Gravity Turn")
    apoapsis = IntPrompt.ask("[text]Target apoapsis (km)", default=90)
    direction = Prompt.ask(
        "[text]Launch direction",
        choices=["e", "w", "n", "s", "ne", "nw", "se", "sw"],
        default="e",
    )
    log.mission_start("Gravity Turn")
    execute_gravity_turn(apoapsis, direction)
    log.mission_complete("Gravity Turn")


def execute_hohmann_transfer(target_body_name: str) -> None:
    """Single-call Hohmann transfer."""

    hohmann_transfer_to_target(conn, target_body_name=target_body_name)


def action_hohmann_transfer(console: Console) -> None:
    console.rule("[primary]Hohmann Transfer")
    target_body_name = Prompt.ask("[text]Target body name", default="Mun")
    log.mission_start("Hohmann Transfer")
    execute_hohmann_transfer(target_body_name)
    log.mission_complete("Hohmann Transfer")
