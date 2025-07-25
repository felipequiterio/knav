from utils import SpaceLogger
import time
from core.utils.formulas import (
    calculate_burn_time,
    calculate_propellant_mass_flow_rate,
)
import krpc
import os

# Local logger for helper utilities
logger = SpaceLogger("HELPERS")


# ─────────────────────────── Vessel helpers ─────────────────────────────


def execute_node(
    conn, vessel, node, precision_threshold=1.0, throttle_margin=5.0, time_margin=5.0
):
    """
    Precisely execute a maneuver node with proper burn timing calculation.

    Parameters
    ----------
    vessel : krpc.Vessel
        The vessel that will execute the maneuver
    node : krpc.Node
        The maneuver node to execute
    precision_threshold : float, optional
        Remaining delta-v threshold for burn completion (m/s). Default: 1.0
    throttle_margin : float, optional
        Remaining delta-v when to switch to precision throttle (m/s). Default: 5.0
    time_margin : float, optional
        Time margin before burn start for final preparations (s). Default: 5.0

    Returns
    -------
    dict
        Execution statistics including predicted vs actual delta-v
    """

    # Get connection from vessel
    body = vessel.orbit.body

    # Calculate burn parameters
    delta_v = node.delta_v
    Isp = vessel.specific_impulse  # [s]
    g0 = body.surface_gravity  # [m/s²]
    m0 = vessel.mass  # [kg]
    thrust = vessel.available_thrust  # [N]

    if thrust <= 0:
        raise ValueError("No available thrust - check that engines are active")

    # Calculate propellant mass flow rate and burn time
    m_dot = calculate_propellant_mass_flow_rate(thrust, Isp, g0)
    burn_time = calculate_burn_time(m_dot, m0, delta_v, Isp, g0)

    current_ut = conn.space_center.ut
    time_to_node = node.ut - current_ut
    logger.status("Node execution planned:")
    logger.status(f"  • Delta-v required: {delta_v:.1f} m/s")
    logger.status(f"  • Burn time: {burn_time:.1f} s")
    logger.status(f"  • Node time: UT {node.ut:.1f}")
    logger.status(f"  • Current UT: {current_ut:.1f}")
    kerbin_day_seconds = 6 * 3600  # 6 hours per Kerbin day
    days = int(time_to_node // kerbin_day_seconds)
    hours = (time_to_node % kerbin_day_seconds) / 3600
    logger.status(f"  • Time until node: {time_to_node:.1f} s ({days}d {hours:.2f} h)")

    # Calculate burn start time (center the burn on the node)
    burn_start_ut = node.ut - burn_time / 2
    warp_to_ut = burn_start_ut - time_margin

    # Warp to pre-burn position
    current_ut = conn.space_center.ut
    if warp_to_ut > current_ut:
        logger.warp(
            f"Warping to T-{burn_time / 2 + time_margin:.1f}s (UT={warp_to_ut:.1f})"
        )
        conn.space_center.warp_to(warp_to_ut)

    # Align with maneuver node direction
    logger.align("Aligning with node direction via SAS")
    vessel.auto_pilot.disengage()
    control_sas(vessel, "maneuver")

    # Give SAS time to settle on node direction
    time.sleep(6)

    # Set up remaining delta-v stream for precision
    remaining_dv = conn.add_stream(getattr, node, "remaining_delta_v")

    # Wait for burn start time
    while conn.space_center.ut < burn_start_ut:
        time.sleep(0.1)

    # Execute the burn
    logger.burn(f"Node execution initiated - {delta_v:.1f} m/s burn")
    initial_dv = remaining_dv()

    # Main burn phase at full throttle
    vessel.control.throttle = 1.0
    while remaining_dv() > throttle_margin:
        time.sleep(0.05)

    # Precision phase with reduced throttle
    logger.burn(f"Entering precision phase - {remaining_dv():.1f} m/s remaining")
    vessel.control.throttle = 0.1
    while remaining_dv() > precision_threshold:
        time.sleep(0.05)

    # Shutdown
    vessel.control.throttle = 0.0
    final_dv_remaining = remaining_dv()

    # Clean up SAS
    vessel.control.sas = False
    vessel.control.sas_mode = vessel.control.sas_mode.stability_assist
    time.sleep(0.5)

    # Calculate execution statistics
    dv_predicted = delta_v
    dv_actual = initial_dv - final_dv_remaining
    dv_residual = final_dv_remaining
    accuracy = (dv_actual / dv_predicted) * 100 if dv_predicted > 0 else 100

    logger.status("Node execution completed!")
    logger.status(f"  • Predicted Δv: {dv_predicted:.1f} m/s")
    logger.status(f"  • Actual Δv: {dv_actual:.1f} m/s")
    logger.status(f"  • Residual Δv: {dv_residual:.2f} m/s")
    logger.status(f"  • Accuracy: {accuracy:.1f}%")

    # Remove the executed node
    node.remove()

    return {
        "predicted_dv": dv_predicted,
        "actual_dv": dv_actual,
        "residual_dv": dv_residual,
        "accuracy_percent": accuracy,
        "burn_time_actual": time.time() - burn_start_ut,  # Approximate
    }


def execute_current_node():
    """
    Execute the current node of the vessel.
    """

    conn = krpc.connect(
        name="Execute current node",
        address=os.getenv("IP"),
        rpc_port=8075,
        stream_port=8076,
    )
    vessel = conn.space_center.active_vessel
    node = vessel.control.nodes[0]
    execute_node(conn, vessel, node)


def control_sas(vessel, mode: str = "stability"):
    """Enable SAS and switch to the specified *mode*.

    Parameters
    ----------
    vessel : krpc.Vessel
        The active vessel instance whose SAS should be configured.
    mode : str, optional
        One of the KSP/-kRPC SAS mode names: ``stability`` (default),
        ``prograde``, ``retrograde``, ``normal``, ``antinormal``,
        ``radial``, ``antiradial``, ``maneuver``.
    """

    # Mapping from human-readable names to kRPC SASMode enum members
    sas = vessel.control.sas_mode
    mapping = {
        "stability": sas.stability_assist,
        "stability_assist": sas.stability_assist,
        "prograde": sas.prograde,
        "retrograde": sas.retrograde,
        "normal": sas.normal,
        "antinormal": sas.anti_normal
        if hasattr(sas, "anti_normal")
        else sas.anti_normal,  # compatibility
        "radial": sas.radial,
        "antiradial": sas.anti_radial
        if hasattr(sas, "anti_radial")
        else sas.anti_radial,
        "maneuver": sas.maneuver,
    }

    if mode not in mapping:
        valid = ", ".join(mapping.keys())
        raise ValueError(f"Invalid SAS mode '{mode}'. Valid modes: {valid}")

    vessel.control.sas = True  # ensure SAS is enabled
    vessel.control.sas_mode = mapping[mode]

    logger.sas(f"SAS enabled — mode set to '{mode}'.")


def change_vessel_name(vessel, new_name):
    logger.info(f"Vessel name before: {vessel.name}")
    vessel.name = new_name
    logger.info(f"Vessel name after: {vessel.name}")


def get_vessel_experiments(vessel):
    """
    Return a list of all Experiment objects on the vessel.
    """
    return vessel.parts.experiments


def get_experiment_info(experiment):
    """
    Return a dictionary of key information about an experiment.
    """
    return {
        "part": experiment.part,
        "name": experiment.name,
        "title": experiment.title,
        "deployed": experiment.deployed,
        "rerunnable": experiment.rerunnable,
        "inoperable": experiment.inoperable,
        "has_data": experiment.has_data,
        "biome": experiment.biome,
        "available": experiment.available,
        "science_subject": experiment.science_subject,
        "data_count": len(experiment.data) if experiment.has_data else 0,
    }


def run_experiment(experiment):
    """
    Run the experiment.
    """
    experiment.run()


def transmit_experiment(experiment):
    """
    Transmit all experimental data contained by this part.
    """
    experiment.transmit()


def dump_experiment(experiment):
    """
    Dump the experimental data contained by the experiment.
    """
    experiment.dump()


def reset_experiment(experiment):
    """
    Reset the experiment.
    """
    experiment.reset()


def experiment_has_data(experiment):
    """
    Return True if the experiment contains data.
    """
    return experiment.has_data


def get_experiment_data(experiment):
    """
    Return the data contained in this experiment (list of ScienceData).
    """
    return experiment.data


def experiment_is_available(experiment):
    """
    Return True if the experiment is available given the current conditions.
    """
    return experiment.available


def experiment_is_rerunnable(experiment):
    """
    Return True if the experiment can be re-run.
    """
    return experiment.rerunnable


def experiment_is_inoperable(experiment):
    """
    Return True if the experiment is inoperable.
    """
    return experiment.inoperable


def experiment_biome(experiment):
    """
    Return the name of the biome the experiment is currently in.
    """
    return experiment.biome


def experiment_science_subject(experiment):
    """
    Return the ScienceSubject for the experiment, or None if unavailable.
    """
    return experiment.science_subject
