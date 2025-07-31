import sys
import os
from pathlib import Path

# Add project root to Python path so we can import from core module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
)
from textual.containers import Container, ScrollableContainer
from maneuver_tabs import (
    GravityTurnTabContainer,
    CircularizationTabContainer,
    HohmannTransferTabContainer,
    LandingTabContainer,
)
import krpc


# --- Main header -------------------------------------------------------------
class AppHeader(Header):
    DEFAULT_CSS = """
    AppHeader {
        height: 3;
        width: 1fr;
        dock: top;
        background: #000000;
        color: #FFFFFF;
        border: #FFFFFF;
        content-align: center middle;
        text-style: bold;
    }
    """


# --- Main footer -------------------------------------------------------------
class AppFooter(Footer):
    DEFAULT_CSS = """
    AppFooter {
        height: 3;
        dock: bottom;
        background: #000000;
        color: #FFFFFF;
        border: #FFFFFF;
        content-align: center middle;
        text-style: italic;
    }
    """


# --- Main content container -------------------------------------------------------------
class ContentContainer(Container):
    DEFAULT_CSS = """
    ContentContainer {
        height: 1fr;
        width: 1fr;
        background: #000000;
        color: #FFFFFF;
        # border: #FFFFFF;
    }
    """

    def compose(self) -> ComposeResult:
        yield LogContainer(id="LogContainer")
        yield GeneralTabContainer(id="GeneralTabContainer")
        yield ManeuversTabContainer(id="ManeuversTabContainer")


# --- Log container (right side of the main container) -------------------------------------------------------------
class LogContainer(ScrollableContainer):
    DEFAULT_CSS = """
    LogContainer {
        height: 1fr;
        width: 30%;
        dock: right;
        background: #000000;
        color: #FFFFFF;
        border: #FFFFFF;
        text-style: bold;
    }
    """


# --- Main container (left upper side of the main container) -------------------------------------------------------------
class GeneralTabContainer(Container):
    DEFAULT_CSS = """
    GeneralTabContainer {
        height: 50%;
        width: 1fr;
        background: #000000;
        color: #FFFFFF;
        border: #FFFFFF;
    }
    
    GeneralTabContainer TabbedContent {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="science"):
            with TabPane("Science", id="science"):
                # yield ScienceTabContainer(id="ScienceContent")
                yield Container(id="ScienceContent")
            with TabPane("Telemetry", id="telemetry"):
                yield Container(id="TelemetryContent")
            with TabPane("Health", id="health"):
                yield Container(id="HealthContent")


# --- Maneuvers tab container (left lower side of the main container) -------------------------------------------------------------
class ManeuversTabContainer(Container):
    DEFAULT_CSS = """
    ManeuversTabContainer {
        height: 50%;
        width: 1fr;
        background: #000000;
        color: #FFFFFF;
        border: #FFFFFF;
    }
    
    ManeuversTabContainer TabbedContent {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="gravity_turn"):
            with TabPane("GRAVITY TURN", id="gravity_turn"):
                yield GravityTurnTabContainer(id="GravityTurnTabContainer")
            with TabPane("CIRCULARIZATION", id="circularization"):
                yield CircularizationTabContainer(id="CircularizationTabContainer")
            with TabPane("HOHMANN TRANSFER", id="hohmann_transfer"):
                yield HohmannTransferTabContainer(id="HohmannTransferTabContainer")
            with TabPane("LANDING", id="landing"):
                yield LandingTabContainer(id="LandingTabContainer")


from dotenv import load_dotenv

load_dotenv()

conn = krpc.connect(
    name="App Connection",
    address=os.getenv("IP"),
    rpc_port=8077,
    stream_port=8078,
)


# --- Main app -------------------------------------------------------------
class AutopilotApp(App):
    def compose(self) -> ComposeResult:
        yield AppHeader(id="AppHeader", show_clock=True)
        yield ContentContainer(id="ContentContainer")
        yield AppFooter(id="AppFooter")

    def on_mount(self) -> None:
        self.title = "KNAV Autopilot"
        if conn.krpc.get_status() is not None:
            self.sub_title = "Connected!"
        else:
            self.sub_title = "Disconnected! (Check your connection)"


if __name__ == "__main__":
    app = AutopilotApp()
    app.run()
