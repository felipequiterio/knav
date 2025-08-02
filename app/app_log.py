"""Rich-powered logger for the KSP autopilot

This module provides an `AppLogger` class that is API-compatible with the
former `SpaceLogger` (see top-level *log.py*) but relies on the fantastic Rich
ecosystem for much nicer formatting:

• Uses `rich.logging.RichHandler` so every log record is rendered through Rich
  with colours, emojis and timestamps.
• High-level helper methods (`mission_start`, `burn`, `telemetry`, …) wrap the
  standard logging calls to keep the terse syntax that is already used all over
  the code-base.
• Live telemetry data are rendered via a Rich `Table` that is *updated in
  place* using the ``cursor`` library. This means the table does not flicker
  and the terminal does not get flooded with successive full copies of the
  table – only the changed values are re-drawn.

The class can safely be instantiated multiple times with different logger
names – handlers are kept per-logger so you will never get duplicate log
records.

Example
-------
```
from app.app_log import AppLogger

log = AppLogger(__name__)
log.mission_start("GRAVITY TURN")
log.burn("Ignition!")

# Live telemetry -------------------------------------------------------
for t in range(5):
    log.telemetry({
        "Time": f"{t}s",
        "Ap":   f"{100 + t*10} km",
        "Pe":   f"{90} km",
    })
    time.sleep(1)

log.mission_complete("GRAVITY TURN")
```
"""

from __future__ import annotations

import logging
from typing import Dict, Any

import curses
import sys
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# Lightweight replacement for the external ``cursor`` dependency using the
# standard library's *curses* capabilities.  We expose a subset of the original
# API (``hide()``, ``show()``, ``move_up()``) that is sufficient for the
# telemetry rendering below.
curses.setupterm()  # Initialise so *tigetstr* works even outside full-screen mode


class _Cursor:
    """Minimal cursor control helper based on *curses* escape sequences."""

    @staticmethod
    def hide() -> None:
        seq = curses.tigetstr("civis") or b"\033[?25l"
        sys.stdout.write(seq.decode())
        sys.stdout.flush()

    @staticmethod
    def show() -> None:
        seq = curses.tigetstr("cnorm") or b"\033[?25h"
        sys.stdout.write(seq.decode())
        sys.stdout.flush()

    @staticmethod
    def move_up(n: int) -> None:
        cuu = curses.tigetstr("cuu") or b""
        if cuu:
            seq = curses.tparm(cuu, n)
            sys.stdout.write(seq.decode())
        else:
            sys.stdout.write(f"\033[{n}A")
        sys.stdout.flush()


# Expose an alias so the rest of the module can continue to use ``cursor.*``
cursor = _Cursor

try:
    # Re-use the Gruvbox theme the TUI already employs (if available)
    from app.theme import GRUVBOX_DARK_THEME as _DEFAULT_THEME
except ModuleNotFoundError:  # Fallback if someone imports this logger stand-alone
    _DEFAULT_THEME = Theme({})

# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------

_ICON = {
    # Generic log levels / statuses
    "INFO": "🟢",
    "WARN": "⚠️ ",
    "ERR ": "🔴",
    "ERR": "🔴",  # alias without padding
    "DBUG": "🔍",
    # Domain-specific short tags (all max 4 chars)
    "STAT": "📊",
    "BURN": "🔥",
    "MNVR": "⚙️ ",
    "ALGN": "🎯",
    "ALIGN": "🎯",  # alias used by helper method
    "FRNG": "🛡️ ",
    "STG ": "🔧",
    "STG": "🔧",  # alias without padding
    "WARP": "⏩",
    "APLT": "🤖",
    "SAS ": "🧭",
    "SAS": "🧭",
}


class _SingleLineFormatter(logging.Formatter):
    """Return only the *message* part – RichHandler adds colours & time-stamp."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        return record.getMessage()


# ---------------------------------------------------------------------------
#  Public logger façade
# ---------------------------------------------------------------------------


class AppLogger:  # pylint: disable=too-many-public-methods
    """Rich-powered logger wrapper used throughout the autopilot."""

    # --------------------------------------------------------------------- init
    def __init__(self, name: str | None = None, theme: Theme | None = None):
        self.console: Console = Console(theme=theme or _DEFAULT_THEME)
        self.logger: logging.Logger = logging.getLogger(name or __name__)
        self.logger.setLevel(logging.INFO)

        # Clear pre-existing handlers when the module is re-imported inside REPLs.
        self.logger.handlers.clear()

        handler = RichHandler(
            console=self.console, show_path=False, markup=True, log_time_format="[%X]"
        )
        handler.setFormatter(_SingleLineFormatter())
        self.logger.addHandler(handler)

        # Telemetry state --------------------------------------------------
        self._telemetry_active: bool = False
        self._telemetry_lines: int = 0  # Number of lines the table occupies

    # ------------------------------------------------------------- high-level API
    # Generic helpers ---------------------------------------------------------
    def _log(self, level: str, tag: str, msg: str, *args: Any, **kwargs: Any) -> None:
        """Internal helper that formats and dispatches the log record.

        * Ensures the *tag* field is padded or trimmed to **exactly four** characters
          so that the subsequent message text is neatly aligned across log lines.
        * Retrieves the corresponding *emoji* from :data:`_ICON`, falling back to an
          empty string if none is defined.
        """
        tag_fmt: str = tag[:4].ljust(4)  # fixed-width tag for alignment
        icon = _ICON.get(tag, _ICON.get(tag_fmt.strip(), ""))
        getattr(self.logger, level.lower())(
            f"{icon} [{tag_fmt}] {msg}", *args, **kwargs
        )

    # Convenience wrappers ----------------------------------------------------
    def mission_start(self, name: str) -> None:
        """Log mission start with a fancy banner."""
        bar = "═" * 70
        self.console.print()  # blank line so the panel stands alone
        self.console.print(
            Panel(f"   {name}  Initiated", style="accent", border_style="primary")
        )
        self.console.print(bar, style="primary")

    def mission_complete(self, name: str) -> None:
        """Log mission completion with a fancy banner."""
        bar = "═" * 70
        self.console.print(
            Panel(
                f"   {name}  Completed Successfully",
                style="success",
                border_style="primary",
            )
        )
        self.console.print(bar, style="primary")

    # Standard log levels -----------------------------------------------------
    def info(self, msg: str) -> None:  # noqa: D401 – imperative mood in public API
        self._log("INFO", "INFO", msg)

    def warning(self, msg: str) -> None:
        self._log("WARNING", "WARN", msg)

    def error(self, msg: str) -> None:
        self._log("ERROR", "ERR", msg)

    def debug(self, msg: str) -> None:
        # Not visible by default – enable via *logging.basicConfig(level=logging.DEBUG)*
        self._log("DEBUG", "DBUG", msg)

    # Domain-specific helpers --------------------------------------------------
    def status(self, msg: str) -> None:
        self._log("INFO", "STAT", msg)

    def maneuver(self, msg: str) -> None:
        self._log("INFO", "MNVR", msg)

    def align(self, msg: str) -> None:
        self._log("INFO", "ALIGN", msg)

    def fairing(self, msg: str) -> None:
        self._log("INFO", "FRNG", msg)

    def stage(self, msg: str) -> None:
        self._log("INFO", "STG", msg)

    def auto_pilot(self, msg: str) -> None:
        self._log("INFO", "APLT", msg)

    def sas(self, msg: str) -> None:
        self._log("INFO", "SAS", msg)

    def burn(self, msg: str) -> None:
        self._log("INFO", "BURN", msg)

    def warp(self, msg: str) -> None:
        self._log("INFO", "WARP", msg)

    # ---------------------------------------------------------------- layout
    @staticmethod
    def _build_table(data: Dict[str, Any]) -> Table:
        """Return a Rich *Table* from the given key/value mapping."""
        table = Table(expand=False, show_edge=True, header_style="primary")
        table.add_column("Parameter", style="secondary")
        table.add_column("Value", style="text", justify="right")

        for key, value in data.items():
            table.add_row(str(key), str(value))

        return table

    # ---------------------------------------------------------------- telemetry
    def telemetry(self, data: Dict[str, Any]) -> None:
        """Render *live* telemetry as a table.

        The first invocation prints the table normally.  Subsequent calls move the
        cursor back to the start of the table and redraw it in place, resulting in
        a smooth in-place update without the need to clear the screen.
        """

        table = self._build_table(data)

        # Render to a string first so we know how *many* lines it spans,
        # and prepend a timestamp so it lines up with other log entries.
        with self.console.capture() as capture:
            self.console.print(table, end="")  # Rich already adds trailing newline
        table_str: str = capture.get()

        # Prefix each line with the current time (no date)
        time_prefix: str = datetime.now().strftime("[%X] ")
        table_str = (
            "\n".join(f"{time_prefix}{line}" for line in table_str.splitlines()) + "\n"
        )
        num_lines: int = table_str.count("\n")  # includes final newline

        if self._telemetry_active:
            # Move the cursor back to the *start* of the previous table and hide it
            cursor.hide()
            cursor.move_up(self._telemetry_lines)

        # Actually print the freshly rendered table
        sys.stdout.write(table_str)
        sys.stdout.flush()

        # Record line-count for the next update cycle and show the cursor again.
        self._telemetry_lines = num_lines
        self._telemetry_active = True
        cursor.show()


# Public convenience function -------------------------------------------------


def get_logger(name: str | None = None) -> AppLogger:  # noqa: D401 – factory
    """Return an :class:`AppLogger` pre-configured with the project theme."""

    return AppLogger(name=name)
