from textual.containers import Container, ScrollableContainer, Horizontal
from textual.widgets import (
    Label,
    Button,
    DataTable,
    Log,
    Static,
    Collapsible,
    OptionList,
    Switch,
)
from textual.app import ComposeResult
import krpc
import os
import sys

# Add parent directory to path to import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.helpers import (
    get_vessel_experiments,
    get_experiment_info,
    run_experiment,
    transmit_experiment,
    dump_experiment,
    reset_experiment,
    experiment_has_data,
    experiment_is_available,
    experiment_is_rerunnable,
    experiment_biome,
)


class ScienceTabContainer(Container):
    DEFAULT_CSS = """
    ScienceTabContainer {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield ScienceControlContainer(id="ScienceControlContainer")
        yield ScienceDataContainer(id="ScienceDataContainer")


class ScienceControlContainer(ScrollableContainer):
    DEFAULT_CSS = """
    ScienceControlContainer {
        height: 1fr;
        width: 50%;
        dock: left;
        border: #FFFFFF;
    }
    
    ScienceControlContainer Button {
        margin: 1 1;
        width: 1fr;
    }

    ScienceControlContainer Switch {
        margin: 1 1;
        width: 1fr;
    }
    ScienceControlContainer Collapsible {
        margin: 1 1;
        width: 1fr;
    }
    ScienceControlContainer DataTable {
        margin: 1 1;
        width: 1fr;
        height: 20;
    }


    """

    def compose(self) -> ComposeResult:
        if science_manager.connect():
            vessel_biome = science_manager.get_current_biome()
            vessel_situation = science_manager.vessel.situation.name
            experiments = science_manager.vessel.parts.experiments
        else:
            vessel_biome = "No Connection"
            vessel_situation = "No Connection"

        with Horizontal():
            yield Label("CURRENT BIOME: ")
            yield Static(vessel_biome, id="current_biome")

        with Horizontal():
            yield Label("CURRENT SITUATION: ")
            yield Static(vessel_situation, id="current_situation")

        yield Label("EXPERIMENT STATUS: ")
        yield DataTable(id="experiments_table")

        yield Label("EXPERIMENT ACTIONS:")
        with Horizontal():
            yield Button("Run Available", id="run_available", disabled=False)
            yield Button("Run Selected", id="run_selected", disabled=True)

        with Horizontal():
            yield Button("Transmit All", id="transmit_all", disabled=False)
            yield Button("Transmit Selected", id="transmit_selected", disabled=True)

        with Horizontal():
            yield Button("Dump All", id="dump_all", disabled=False)
            yield Button("Reset All", id="reset_all", disabled=False)

        yield Label("AUTO-SCIENCE OPTIONS:")
        yield Switch(value=False, id="auto_run_switch")
        yield Label("Auto-run available experiments")

        yield Switch(value=False, id="auto_transmit_switch")
        yield Label("Auto-transmit completed experiments")

        with Collapsible(collapsed=True, title="Experiment Filters"):
            yield OptionList(
                "Show All",
                "Available Only",
                "With Data Only",
                "Deployed Only",
                "Rerunnable Only",
                id="experiment_filter",
            )

        yield Button("Refresh Experiments", id="refresh_experiments", disabled=False)


class ScienceDataContainer(Container):
    DEFAULT_CSS = """
    ScienceDataContainer {
        height: 1fr;
        width: 50%;
        dock: right;
        border: #FFFFFF;
    }
    
    ScienceDataContainer Log {
        height: 1fr;
        width: 1fr;
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("SCIENCE LOG:", classes="data-label")
        yield Log(id="science_log", auto_scroll=True)


# Additional helper classes for the science tab functionality
class ScienceManager:
    """Helper class to manage science operations and data"""

    def __init__(self):
        self.conn = None
        self.vessel = None
        self.experiments = get_vessel_experiments(self.vessel)

    def connect(self):
        """Establish connection to KSP"""
        try:
            self.conn = krpc.connect(
                name="Science Manager",
                address=os.getenv("IP"),
                rpc_port=8077,
                stream_port=8078,
            )
            self.vessel = self.conn.space_center.active_vessel
            return True
        except Exception:
            return False

    def get_current_biome(self):
        """Get the current biome name"""
        if not self.vessel:
            return "No Connection"
        try:
            # Get biome from any experiment that has it, or return surface biome
            experiments = get_vessel_experiments(self.vessel)
            if experiments:
                return experiment_biome(experiments[0])
            return "Unknown"
        except:
            return "Unknown"

    def refresh_experiments(self):
        """Refresh the list of experiments"""
        if not self.vessel:
            return []

        try:
            self.experiments = get_vessel_experiments(self.vessel)
            return [get_experiment_info(exp) for exp in self.experiments]
        except:
            return []

    def run_available_experiments(self):
        """Run all available experiments"""
        results = []
        for exp in self.experiments:
            if experiment_is_available(exp) and not experiment_has_data(exp):
                try:
                    run_experiment(exp)
                    info = get_experiment_info(exp)
                    results.append(f"✓ Ran: {info['title']}")
                except Exception as e:
                    info = get_experiment_info(exp)
                    results.append(f"✗ Failed: {info['title']} - {str(e)}")
        return results

    def transmit_all_data(self):
        """Transmit all experiment data"""
        results = []
        for exp in self.experiments:
            if experiment_has_data(exp):
                try:
                    transmit_experiment(exp)
                    info = get_experiment_info(exp)
                    results.append(f"📡 Transmitted: {info['title']}")
                except Exception as e:
                    info = get_experiment_info(exp)
                    results.append(f"✗ Failed: {info['title']} - {str(e)}")
        return results

    def dump_all_data(self):
        """Dump all experiment data"""
        results = []
        for exp in self.experiments:
            if experiment_has_data(exp):
                try:
                    dump_experiment(exp)
                    info = get_experiment_info(exp)
                    results.append(f"🗑️ Dumped: {info['title']}")
                except Exception as e:
                    info = get_experiment_info(exp)
                    results.append(f"✗ Failed: {info['title']} - {str(e)}")
        return results

    def reset_all_experiments(self):
        """Reset all experiments"""
        results = []
        for exp in self.experiments:
            if experiment_is_rerunnable(exp):
                try:
                    reset_experiment(exp)
                    info = get_experiment_info(exp)
                    results.append(f"🔄 Reset: {info['title']}")
                except Exception as e:
                    info = get_experiment_info(exp)
                    results.append(f"✗ Failed: {info['title']} - {str(e)}")
        return results


science_manager = ScienceManager()
