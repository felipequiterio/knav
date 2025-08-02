import os
import sys
from typing import List, Callable
import krpc
from rich import box
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console
from rich.table import Table
from app.theme import GRUVBOX_DARK_THEME
from app.actions import action_gravity_turn

# --- Console ----------
console = Console(theme=GRUVBOX_DARK_THEME)


def gravity_turn():
    action_gravity_turn(console)


# --- KRPC connection -----
def connect() -> krpc.Client:
    """Establish (or reuse) a connection to the running KRPC server."""

    ip = os.getenv("IP", "127.0.0.1")
    try:
        return krpc.connect(
            name="KSP Autopilot TUI",
            address=ip,
            rpc_port=8077,
            stream_port=8078,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(
            Panel(
                f"[danger]Cannot connect to KRPC at {ip}:8077 – {exc}",
                title="Connection failed",
                style="danger",
            )
        )
        sys.exit(2)


MENU_ENTRIES: List[tuple[str, str, Callable[[], None]]] = [
    ("1", "Gravity Turn", gravity_turn),
    # ("2", "Hohmann Transfer", action_hohmann_transfer),
    # ("3", "Execute Maneuver Node", action_execute_node),
    # ("4", "Change Vessel Name", action_change_vessel_name),
    # ("5", "Science Experiments", action_experiment_overview),
    ("q", "Quit", lambda: sys.exit(0)),
]


def render_home() -> None:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=1),
    )

    # Header – App title
    layout["header"].update(
        Panel(
            "[primary bold]🚀  KSP Autopilot  ✦  [secondary]Terminal UI",
            style="accent",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )

    # Body – Menu table
    body_table = Table.grid(padding=1)
    for key, label, _func in MENU_ENTRIES:
        body_table.add_row(f"[secondary]{key}[/secondary]", f"[text]{label}")

    layout["body"].update(Panel(body_table, title="[accent]Menu", box=box.SIMPLE_HEAVY))

    # Footer – hint
    layout["footer"].update(
        Panel(
            "[comment]Choose an option and press <enter>",
            style="comment",
            box=box.SQUARE,
            padding=(0, 1),
        )
    )

    console.print(layout)


conn: krpc.Client | None = None  # Will be initialised in `run()`


def run() -> None:
    global conn
    conn = connect()

    while True:
        console.clear()
        render_home()

        choice = Prompt.ask(
            "", choices=[key for key, _, _ in MENU_ENTRIES], default="q"
        )
        chosen = next(func for key, _label, func in MENU_ENTRIES if key == choice)
        console.clear()
        try:
            chosen()
        except Exception as exc:
            console.print(Panel(f"[danger]Error: {exc}", title="Crash", style="danger"))
        finally:
            if choice != "q":
                console.print()
                input("[comment]Press <enter> to return to menu…")
