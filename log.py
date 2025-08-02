import logging
import sys

# ── ANSI palette ────────────────────────────────────────────────────────────────
RESET, BOLD = "\033[0m", "\033[1m"
CYAN, YELLOW, RED, GREEN, MAGENTA, BLUE, WHITE, ORANGE = (
    "\033[36m",
    "\033[33m",
    "\033[31m",
    "\033[32m",
    "\033[35m",
    "\033[34m",
    "\033[37m",
    "\033[38;5;208m",
)

LEVEL_COLORS = {
    "INFO": CYAN,
    "WARNING": YELLOW,
    "ERROR": RED,
    "DEBUG": MAGENTA,
}


# ── Custom formatter ────────────────────────────────────────────────────────────
class ColorFormatter(logging.Formatter):
    """
    Timestamp │ (level |) message
    Level is suppressed for plain INFO lines to avoid the repeated "| INFO |".
    """

    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelname, WHITE)
        ts = f"{BOLD}{self.formatTime(record, self.datefmt)}{RESET}"

        # Only show the level column for non-INFO records
        level_part = (
            f"{color}{record.levelname}{RESET} │ " if record.levelname != "INFO" else ""
        )

        msg = f"{color}{record.getMessage()}{RESET}"
        return f"{ts} │ {level_part}{msg}"


# ── Logger wrapper ──────────────────────────────────────────────────────────────
class SpaceLogger:
    """
    A specialized logger for space operations with custom formatting and methods.

    Usage:
        log = SpaceLogger(__name__)
        log.mission_start("GRAVITY TURN")
        log.burn("Ignition!")
        log.telemetry({"altitude": "100km"})
        ...
    """

    # --------------------------------------------------------------------- init
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers when the module is re-imported
        self.logger.handlers.clear()

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(ColorFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        self.logger.addHandler(ch)

    # ------------------------------------------------------------- high-level API
    def mission_start(self, name):
        """Log mission start with a banner."""
        self._banner(name, "INITIATED", BLUE)

    def mission_complete(self, name):
        """Log mission completion with a banner."""
        self._banner(name, "COMPLETED SUCCESSFULLY", GREEN)

    def info(self, msg):
        """Log general information."""
        self.logger.info(f"🟢 [INFO] {msg}")

    def warning(self, msg):
        """Log a warning message."""
        self.logger.warning(f"⚠️ [WARN] {msg}")

    def error(self, msg):
        """Log an error message."""
        self.logger.error(f"🔴 [ERR ] {msg}")

    def debug(self, msg):
        """Log a debug message."""
        self.logger.debug(f"🔍 [DBUG] {msg}")

    def status(self, msg):
        """Log a status update."""
        self.logger.info(f"📊 [STAT] {msg}")

    def telemetry(self, data: dict):
        """Log telemetry data in a formatted table."""
        # Create the table first
        table = self._table(data)

        # Format the entire telemetry block
        telemetry_block = (
            f"\n{BOLD}{MAGENTA}{'─' * 70}{RESET}\n"
            f"📡 {BOLD}TELEMETRY:{RESET}\n"
            f"{table}\n"
            f"{BOLD}{MAGENTA}{'─' * 70}{RESET}"
        )

        # Log it as a single message
        self.logger.info(telemetry_block)

    def maneuver(self, msg):
        """Log a maneuver message."""
        self.logger.info(f"⚙️ [MNVR] {msg}")

    def align(self, msg):
        """Log an align message."""
        self.logger.info(f"🎯 [ALGN] {msg}")

    def fairing(self, msg):
        """Log a fairing message."""
        self.logger.info(f"🛡️ [FRNG] {msg}")

    def stage(self, msg):
        """Log a stage message."""
        self.logger.info(f"🔧 [STG ] {msg}")

    def auto_pilot(self, msg):
        """Log an auto pilot message."""
        self.logger.info(f"🤖 [APLT] {msg}")

    def sas(self, msg):
        """Log a SAS message."""
        self.logger.info(f"🧭 [SAS ] {msg}")

    def burn(self, msg):
        """Log a burn message."""
        self.logger.info(f"🔥 [BURN] {msg}")

    def warp(self, msg):
        """Log a warp message."""
        self.logger.info(f"⏩ [WARP] {msg}")

    # ---------------------------------------------------------------- internals
    def _banner(self, mission, state, color):
        """Create a mission banner with the given state."""
        bar = f"{color}{'═' * 70}{RESET}"
        self.logger.info(f"\n{bar}\n🚀 {mission} {state}\n{bar}")

    @staticmethod
    def _table(data: dict) -> str:
        """Format dictionary data as an ASCII table."""
        k_w = max(len(str(k)) for k in data)
        v_w = max(len(str(v)) for v in data.values())
        header = (
            "┌" + "─" * (k_w + 2) + "┬" + "─" * (v_w + 2) + "┐\n"
            "│ " + "Parameter".ljust(k_w) + " │ " + "Value".ljust(v_w) + " │\n"
            "├" + "─" * (k_w + 2) + "┼" + "─" * (v_w + 2) + "┤\n"
        )
        body = "\n".join(
            f"│ {str(k).ljust(k_w)} │ {str(v).ljust(v_w)} │" for k, v in data.items()
        )
        footer = "\n└" + "─" * (k_w + 2) + "┴" + "─" * (v_w + 2) + "┘"
        return header + body + footer
