"""Autopilot TUI powered by Rich

This simple terminal user-interface is meant to demonstrate how you could drive
KSP (Kerbal Space Program) autopilot helpers from the command line.  It leans on
``rich`` for all rendering, tries to stay minimalistic, and embraces the dark
*gruvbox* colour-palette.

The UI is intentionally kept synchronous and blocking; once you grow out of it
consider porting this over to Textual (https://github.com/Textualize/textual)
which will give you much finer-grained control over layout, real-time updates
and mouse support – all while still using Rich under the hood.

Requirements
------------
    pip install rich
    # plus the rest of your project requirements (krpc, etc.)

Run
---
    python -m web_app.app

"""

from __future__ import annotations

import os
import sys
from typing import List

import krpc
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.theme import Theme

# ----------------------------------------------------------------------------
#  1.  Rich configuration (Gruvbox-inspired dark theme)
# ----------------------------------------------------------------------------

GRUVBOX_DARK_THEME = Theme(
    {
        # Darker, more muted Gruvbox palette with burnt reds
        "primary": "bold #a89984",  # muted sand
        "secondary": "#7c2c20",  # burnt red (was dark grey)
        "accent": "#665c54",  # mid dark grey
        "text": "#bdae93",  # light muted
        "comment": "#282828",  # very dark grey
        "danger": "bold #7c2c20",  # burnt red
        "warning": "#af3a03",  # deep burnt orange
        "success": "#6c782e",  # olive green
        "background": "#1d2021",  # Gruvbox darkest background
    }
)

console = Console(theme=GRUVBOX_DARK_THEME)

# Ensure project root is on PYTHONPATH when running the file directly ---------
import pathlib

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ----------------------------------------------------------------------------
#  2.  Project-specific autopilot helpers
# ----------------------------------------------------------------------------

# Import autopilot helpers directly from their proper modules
from core.utils.helpers import (
    execute_current_node,
    change_vessel_name,
    get_vessel_experiments,
    run_experiment,
    transmit_experiment,
    dump_experiment,
    experiment_has_data,
    experiment_is_available,
    experiment_is_rerunnable,
)
from core.launch.gravity_turn import gravity_turn  # noqa: E402  (import order)
from core.orbital.circularization import circularization  # noqa: E402
from core.orbital.ht import hohmann_transfer  # noqa: E402

# Convenience wrappers to preserve the previous higher-level semantics ---------


def execute_gravity_turn(apoapsis: int, direction: str) -> None:
    """Single-call gravity-turn followed by on-orbit circularisation."""

    gravity_turn(target_altitude=apoapsis * 1000, target_direction=direction)
    circularization()


def execute_hohmann_transfer(target_body: str) -> None:
    hohmann_transfer(target_body)


def execute_active_node() -> None:
    execute_current_node()


def change_active_vessel_name(new_name: str) -> None:
    conn.space_center.active_vessel.name = new_name
    change_vessel_name(conn.space_center.active_vessel, new_name)


def get_experiments():
    return get_vessel_experiments(conn.space_center.active_vessel)


def run_experiments(experiments):
    for experiment in experiments:
        run_experiment(experiment)


def transmit_experiments(experiments):
    for experiment in experiments:
        transmit_experiment(experiment)


def dump_experiments(experiments):
    for experiment in experiments:
        dump_experiment(experiment)


def check_experiment_data(experiment):
    return experiment_has_data(experiment)


# ----------------------------------------------------------------------------
#  3.  Connection helpers
# ----------------------------------------------------------------------------


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


conn: krpc.Client | None = None  # Will be initialised in `main()`

# ----------------------------------------------------------------------------
#  4.  High-level actions (wrappers around scratch helpers)
# ----------------------------------------------------------------------------


def action_gravity_turn() -> None:
    console.rule("[primary]Gravity Turn")
    apoapsis = IntPrompt.ask("[text]Target apoapsis (km)", default=90)
    direction = Prompt.ask(
        "[text]Launch direction (e, w, n, s, ne, nw, se, sw)",
        choices=["e", "w", "n", "s", "ne", "nw", "se", "sw"],
        default="e",
    )
    execute_gravity_turn(apoapsis, direction)
    console.print("[success]Gravity turn sequence completed")


def action_hohmann_transfer() -> None:
    console.rule("[primary]Hohmann Transfer")
    target = Prompt.ask(
        "[text]Target celestial body (e.g. Mun, Minmus, Duna)",
        default="Mun",
    )
    execute_hohmann_transfer(target)
    console.print("[success]Hohmann transfer executed")


def action_execute_node() -> None:
    console.rule("[primary]Execute Maneuver Node")
    execute_active_node()
    console.print("[success]Current maneuver node executed")


def action_change_vessel_name() -> None:
    console.rule("[primary]Change Vessel Name")
    vessel = conn.space_center.active_vessel  # type: ignore[union-attr]
    new_name = Prompt.ask("[text]New vessel name", default=vessel.name)
    change_active_vessel_name(new_name)
    console.print(f"[success]Renamed vessel to [accent]{new_name}")


def action_experiment_overview() -> None:
    console.rule("[primary]Science Experiments")
    experiments = get_experiments()

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="secondary", justify="right")
    table.add_column("Name", style="text")
    table.add_column("Has Data", justify="center")
    table.add_column("Available", justify="center")
    table.add_column("Rerunnable", justify="center")

    for idx, exp in enumerate(experiments, start=1):
        # Always use exp.title for the experiment name
        try:
            name = exp.title
        except AttributeError:
            name = str(exp)
        has_data = "✔" if check_experiment_data(exp) else "✘"
        available = "✔" if experiment_is_available(exp) else "✘"
        rerun = "✔" if experiment_is_rerunnable(exp) else "✘"
        table.add_row(
            str(idx),
            name,
            has_data,
            available,
            rerun,
        )

    console.print(table)

    choice = (
        Prompt.ask(
            "[text]Run experiments – enter index, 'a' for all, or leave blank to return",
            default="",
        )
        .strip()
        .lower()
    )

    if choice == "":
        return

    # Determine which experiments to target ---------------------------------
    if choice == "a":
        targets = experiments
    elif choice.isdigit():
        idx = int(choice)
        if not 1 <= idx <= len(experiments):
            console.print("[warning]Index out of range; returning to menu.")
            return
        targets = [experiments[idx - 1]]
    else:
        console.print("[warning]Invalid choice; returning to menu.")
        return

    # Execute selected experiments ------------------------------------------
    run_experiments(targets)
    console.print("[success]Experiments run. Transmitting data…")
    transmit_experiments(targets)
    console.print("[success]Transmission complete. Dumping experiments…")
    dump_experiments(targets)
    console.print("[success]Experiments dumped")


# ----------------------------------------------------------------------------
#  5.  Home screen + menu
# ----------------------------------------------------------------------------

MENU_ENTRIES: List[tuple[str, str, callable[[], None]]] = [
    ("1", "Gravity Turn", action_gravity_turn),
    ("2", "Hohmann Transfer", action_hohmann_transfer),
    ("3", "Execute Maneuver Node", action_execute_node),
    ("4", "Change Vessel Name", action_change_vessel_name),
    ("5", "Science Experiments", action_experiment_overview),
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


# ----------------------------------------------------------------------------
#  6.  Main loop
# ----------------------------------------------------------------------------


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
