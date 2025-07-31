from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, Horizontal
from textual.screen import Screen
from textual.widgets import Placeholder, Tabs, Label, Tab


# --- Main header -------------------------------------------------------------
class Header(Placeholder):
    DEFAULT_CSS = """
    Header {
        height: 3;
        dock: top;
    }
    """


# --- Main footer -------------------------------------------------------------
class Footer(Placeholder):
    DEFAULT_CSS = """
    Footer {
        height: 3;
        dock: bottom;
    }
    """


# --- Main container for the app (hold all widgets for the main page) ------------------------------
class AppMainContainer(Horizontal):
    DEFAULT_CSS = """
    AppMainContainer {
        height: 1fr;
        width: 1fr;
    }
    """


# --- Main container for the log on the right of the app using horizontal scroll for log messages ------------------------------
class LogHorizontalScroll(HorizontalScroll):
    DEFAULT_CSS = """
    LogHorizontalScroll {
        height: 1fr;
        width: 1fr;
    }
    """


class LogContainer(Placeholder):
    DEFAULT_CSS = """
    LogContainer {
        height: 1fr;
        width: 35%;
    }
    """


# --- Main container for the tabs on the left of the app ------------------------------
TABS_NAMES = ["Autopilot", "Science", "Telemetry"]


class TabContainer(Placeholder):
    DEFAULT_CSS = """
    TabContainer {
        height: 1fr;
        width: 65%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Tabs(
            *[Tab(label=tab_name) for tab_name in TABS_NAMES],
            id="main-tabs",
        )
        yield ManeuverTabsContainer(id="ManeuverTabsContainer")
        yield Label("Select a tab to see content", id="content-label")


# --- Main container for the maneuver tabs ------------------------------
MANEUVER_NAMES = ["Maneuver 1", "Maneuver 2", "Maneuver 3"]


class ManeuverTabsContainer(Placeholder):
    DEFAULT_CSS = """
    ManeuverTabsContainer {
        height: auto;
        width: 1fr;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Tabs(
            *[Tab(label=tab_name) for tab_name in MANEUVER_NAMES],
            id="maneuver-tabs",
        )


# --- Main screen for the app ------------------------------
class AutopilotScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with AppMainContainer(id="AppMainContainer"):
            yield TabContainer(id="TabContainer")
            yield LogContainer(id="LogContainer")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        """Initialize the UI state when the screen is mounted."""
        # Hide maneuver tabs initially
        self.query_one("#ManeuverTabsContainer").visible = False

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle TabActivated message sent by Tabs."""
        if event.tab is None:
            return

        # Get the tabs widget to check which one sent the event
        tabs_widget = event.tabs
        tab_label = event.tab.label

        # Handle main tabs
        if tabs_widget.id == "main-tabs":
            self._handle_main_tab_activated(tab_label)
        # Handle maneuver tabs (nested within autopilot)
        elif tabs_widget.id == "maneuver-tabs":
            self._handle_maneuver_tab_activated(tab_label)

    def _handle_main_tab_activated(self, tab_label: str) -> None:
        """Handle activation of main tabs (Autopilot, Science, Telemetry)."""
        content_label = self.query_one("#content-label", Label)
        maneuver_container = self.query_one("#ManeuverTabsContainer")

        if tab_label == "Autopilot":
            # Show maneuver tabs and update content
            maneuver_container.visible = True
            content_label.update("Autopilot mode - select a maneuver below")
        elif tab_label == "Science":
            # Hide maneuver tabs and show science content
            maneuver_container.visible = False
            content_label.update("Science content goes here")
        elif tab_label == "Telemetry":
            # Hide maneuver tabs and show telemetry content
            maneuver_container.visible = False
            content_label.update("Telemetry content goes here")

    def _handle_maneuver_tab_activated(self, tab_label: str) -> None:
        """Handle activation of maneuver tabs within the Autopilot tab."""
        content_label = self.query_one("#content-label", Label)
        content_label.update(f"Autopilot - {tab_label} selected")


class LayoutApp(App):
    def on_ready(self) -> None:
        self.push_screen(AutopilotScreen())


if __name__ == "__main__":
    app = LayoutApp()
    app.run()
