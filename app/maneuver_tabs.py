from textual.containers import (
    Container,
    ScrollableContainer,
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widgets import Label, Input, OptionList, Button, Collapsible
from textual.app import ComposeResult
from textual import work
from textual.worker import Worker, get_current_worker
import dotenv
from app.connection import connect

dotenv.load_dotenv()

# === GRAVITY TURN TAB ==========================================================================================================

conn = connect()
vsl = conn.space_center.active_vessel
body = vsl.orbit.body
nrf = body.non_rotating_reference_frame  # Planet-centred inertial-ish
flt = vsl.flight(nrf)


# --- Gravity Turn Tab Container -------------------------------------------------------------
class GravityTurnTabContainer(Container):
    DEFAULT_CSS = """
    GravityTurnTabContainer {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield GravityTurnManeuverContainer(id="GravityTurnManeuverContainer")
        yield GravityTurnGraphContainer(id="GravityTurnGraphContainer")


class GravityTurnButton(Button):
    DEFAULT_CSS = """
    GravityTurnButton {
        width: 1fr;
    }
    """


class OrbitInsertionButton(Button):
    DEFAULT_CSS = """
    OrbitInsertionButton {
        width: 1fr;
    }
    """
    pass


class FullManeuverButton(Button):
    DEFAULT_CSS = """
    FullManeuverButton {
        width: 1fr;
    }
    """
    pass


# --- Gravity Turn Maneuver Container -------------------------------------------------------------
class GravityTurnManeuverContainer(ScrollableContainer):
    DEFAULT_CSS = """
    GravityTurnManeuverContainer {
        height: 1fr;
        width: 50%;
        dock: left;
        scrollbar-gutter: stable;
    }
    
    GravityTurnManeuverContainer Button {
        margin: 1 1;
        width: 1fr;
    }
    GravityTurnManeuverContainer Input {
        margin: 1 1;
        width: 1fr;
    }
    GravityTurnManeuverContainer Label {
        margin: 0 1;
        width: 1fr;
    }
    GravityTurnManeuverContainer Collapsible {
        margin: 1 1;
        width: 1fr;
    }

    GravityTurnManeuverContainer Vertical {
        height: 1fr;
        width: 1fr;
    }
    
    """
    # Worker set up
    gravity_turn_worker: Worker | None = None
    orbit_insertion_worker: Worker | None = None
    full_maneuver_worker: Worker | None = None

    def compose(self) -> ComposeResult:
        yield Label("TARGET ALTITUDE:")
        yield Input(
            placeholder="150,000m - Input your target altitude",
            id="target_altitude_input",
        )
        yield Label("TARGET DIRECTION:")
        with Collapsible(collapsed=True):
            yield OptionList(
                "North",
                "North-East",
                "East",
                "North-West",
                "West",
                "South-East",
                "South",
                "South-West",
                id="target_direction_optionlist",
            )
        with VerticalScroll():
            yield FullManeuverButton("Full Maneuver", id="full_maneuver_button")
            yield Button("Abort", id="abort_button", disabled=True)
            yield GravityTurnButton("Gravity Turn (only)", id="gravity_turn_button")
            yield OrbitInsertionButton(
                "Orbit Insertion (only)", id="orbit_insertion_button"
            )

    # ------------------- CLICK HANDLER (todos botões) --------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button
        # 1) Gravity Turn
        if button.id == "gravity_turn_button":
            # Disable buttons
            button.disabled = True

            # Start gravity turn worker
            self.gravity_turn_worker = self._gravity_turn()

            # Re-enable buttons
            button.disabled = False
            self.query_one("#abort_button").disabled = True
            self.query_one("#orbit_insertion_button").disabled = True
            self.query_one("#full_maneuver_button").disabled = True

        # 2) Abort
        elif button.id == "abort_button":
            # Cancel all workers
            if self.gravity_turn_worker:
                self.gravity_turn_worker.cancel()
                self._cancel_gravity_turn = True

            if self.orbit_insertion_worker:
                self.orbit_insertion_worker.cancel()
                self._cancel_orbit_insertion = True

            if self.full_maneuver_worker:
                self.full_maneuver_worker.cancel()
                self._cancel_full_maneuver = True

            # Disengage autopilot and throttle
            vsl.control.throttle = 0
            vsl.auto_pilot.disengage()

        # 3) Orbit Insertion
        elif button.id == "orbit_insertion_button":
            button.disabled = True

            self.orbit_insertion_worker = self._orbit_insertion()

        # 4) Full Maneuver
        elif button.id == "full_maneuver_button":
            if self.full_maneuver_worker and self.full_maneuver_worker.is_running:
                return
            button.disabled = True

            self.query_one("#abort_button").disabled = False
            self.full_maneuver_worker = self._full_maneuver()
            button.disabled = False

        # Ensure the state of the buttons is consistent after every press
        self._update_button_states()

    # Add a cancellation flag to the instance
    _cancel_gravity_turn: bool = False

    # ----------------------- BUTTON STATE MANAGEMENT ----------------
    def _any_worker_running(self) -> bool:
        """Return True if any maneuver worker is currently running."""
        return any(
            w and getattr(w, "is_running", False)
            for w in (
                self.gravity_turn_worker,
                self.orbit_insertion_worker,
                self.full_maneuver_worker,
            )
        )

    def _update_button_states(self) -> None:
        """Enable/disable maneuver and abort buttons based on worker state."""
        running = self._any_worker_running()
        # Maneuver buttons should be disabled while a worker is running
        self.query_one("#gravity_turn_button").disabled = running
        self.query_one("#orbit_insertion_button").disabled = running
        self.query_one("#full_maneuver_button").disabled = running
        # Abort button is enabled only when at least one worker is running
        self.query_one("#abort_button").disabled = not running

    # ----------------------- WORKER --------------------------------
    @work(exclusive=True, thread=True, name="gravity_turn")
    def _gravity_turn(self) -> None:
        """
        Executa gravity_turn fora do event-loop.
        Envia `worker.is_cancelled` para permitir abortar com segurança.
        """
        from core.launch.gravity_turn import gravity_turn  # sua função real

        worker = get_current_worker()

        # Pass a cancellation callback to gravity_turn, if possible
        def is_cancelled():
            # Check both the worker and the instance flag
            return worker.is_cancelled or getattr(self, "_cancel_gravity_turn", False)

        try:
            gravity_turn(is_cancelled=is_cancelled)
        except TypeError:
            # Fallback for legacy gravity_turn signature
            gravity_turn()
        finally:
            # Reset the cancellation flag for next run
            self._cancel_gravity_turn = False
            worker.cancel()
            # Schedule UI update back on the main thread
            self.app.call_from_thread(self._update_button_states)

    @work(exclusive=True, thread=True, name="orbit_insertion")
    def _orbit_insertion(self) -> None:
        """
        Executa gravity_turn fora do event-loop.
        Envia `worker.is_cancelled` para permitir abortar com segurança.
        """
        from core.orbital.circularization import circularization  # sua função real

        worker = get_current_worker()

        # Pass a cancellation callback to gravity_turn, if possible
        def is_cancelled():
            # Check both the worker and the instance flag
            return worker.is_cancelled or getattr(self, "_cancel_gravity_turn", False)

        try:
            circularization(is_cancelled=is_cancelled)
        except TypeError:
            circularization()
        finally:
            self._cancel_gravity_turn = False
            worker.cancel()
            # Schedule UI update back on the main thread
            self.app.call_from_thread(self._update_button_states)

    @work(exclusive=True, thread=True, name="full_maneuver")
    def _full_maneuver(self) -> None:
        """
        Executa gravity_turn fora do event-loop.
        Envia `worker.is_cancelled` para permitir abortar com segurança.
        """
        from core.launch.gravity_turn import gravity_turn
        from core.orbital.circularization import circularization

        worker = get_current_worker()

        # Pass a cancellation callback to gravity_turn, if possible
        def is_cancelled():
            # Check both the worker and the instance flag
            return worker.is_cancelled or getattr(self, "_cancel_gravity_turn", False)

        try:
            gravity_turn(is_cancelled=is_cancelled)
            circularization(is_cancelled=is_cancelled)
        except TypeError:
            gravity_turn()
            circularization()
        finally:
            self._cancel_gravity_turn = False
            self._cancel_orbit_insertion = False
            worker.cancel()
            # Schedule UI update back on the main thread
            self.app.call_from_thread(self._update_button_states)


# --- Gravity Turn Graph Container -------------------------------------------------------------
class GravityTurnGraphContainer(Container):
    DEFAULT_CSS = """
    GravityTurnGraphContainer {
        height: 1fr;
        width: 50%;
        dock: right;
        border: #FFFFFF;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Graph will go here")


# === CIRCULARIZATION TAB ==========================================================================================================


# --- Circularization Tab Container -------------------------------------------------------------
class CircularizationTabContainer(Container):
    DEFAULT_CSS = """
    CircularizationTabContainer {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield CircualrizationManeuverContainer(id="CircualrizationManeuverContainer")
        yield CircularizationGraphContainer(id="CircularizationGraphContainer")


# --- Circularization Maneuver Container (container on the left) -------------------------------------------------------------
class CircualrizationManeuverContainer(ScrollableContainer):
    DEFAULT_CSS = """
    CircualrizationManeuverContainer {
        height: 1fr;
        width: 50%;
        dock: left;
    }
    
    CircualrizationManeuverContainer Button {
        margin: 1 1;
        width: 1fr;
    }
    CircualrizationManeuverContainer Input {
        margin: 1 1;
        width: 1fr;
    }
    CircualrizationManeuverContainer Label {
        margin: 0 1;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("TARGET PERIAPSIS ALTITUDE:")
        yield Input(placeholder="150,000m - Input your target periapsis altitude")
        yield Label("TARGET APOSIS ALTITUDE:")
        yield Input(placeholder="150,000m - Input your target aposis altitude")
        with Horizontal():
            yield Button("Calculate Circularization", disabled=False)
            yield Button("Execute Maneuver", disabled=False)


# --- Circularization Graph Container (container on the right) -------------------------------------------------------------
class CircularizationGraphContainer(Container):
    DEFAULT_CSS = """
    CircularizationGraphContainer {
        height: 1fr;
        width: 50%;
        dock: right;
        border: #FFFFFF;
    }
    """


# === HOHMANN TRANSFER TAB ==========================================================================================================


# --- Hohmann Transfer Tab Container -------------------------------------------------------------
class HohmannTransferTabContainer(Container):
    DEFAULT_CSS = """
    HohmannTransferTabContainer {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield HohmannTransferManeuverContainer(id="HohmannTransferManeuverContainer")
        yield HohmannTransferGraphContainer(id="HohmannTransferGraphContainer")


# --- Hohmann Transfer Maneuver Container (container on the left) -------------------------------------------------------------
class HohmannTransferManeuverContainer(ScrollableContainer):
    DEFAULT_CSS = """
    HohmannTransferManeuverContainer {
        height: 1fr;
        width: 50%;
        dock: left;
    }
    HohmannTransferManeuverContainer Button {
        margin: 1 1;
        width: 1fr;
    }
    HohmannTransferManeuverContainer Input {
        margin: 1 1;
        width: 1fr;
    }
    HohmannTransferManeuverContainer Collapsible {
        margin: 1 1;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("TARGET BODY:")
        with Collapsible(collapsed=True):
            yield OptionList(
                "Mun",
                "Minmus",
                "Duna",
                "Ike",
                "Jool",
                "Laythe",
                "Vall",
                "Bop",
                "Pol",
                "Eeloo",
            )
        with Horizontal():
            with Vertical():
                yield Button("Calculate Transfer Maneuver", disabled=False)
                yield Button("Execute Transfer Maneuver", disabled=False)
            with Vertical():
                yield Button("Calculate Insertion Maneuver", disabled=False)
                yield Button("Execute Insertion Maneuver", disabled=False)


# --- Hohmann Transfer Graph Container (container on the right) -------------------------------------------------------------
class HohmannTransferGraphContainer(Container):
    DEFAULT_CSS = """
    HohmannTransferGraphContainer {
        height: 1fr;
        width: 50%;
        dock: right;
        border: #FFFFFF;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Graph will go here")


# === LANDING TAB ==========================================================================================================


# --- Landing Tab Container -------------------------------------------------------------
class LandingTabContainer(Container):
    DEFAULT_CSS = """
    LandingTabContainer {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Landing site coordinates")
        yield OptionList(
            "Powered Landing",
            "Parachute Landing",
            "Atmospheric Entry",
        )
        yield Button("Calculate Landing", disabled=True)
        yield Button("Execute Landing", disabled=True)
