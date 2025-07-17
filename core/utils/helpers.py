from core.utils.logger import logger


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
