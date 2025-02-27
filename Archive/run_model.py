"""
Runner script for Shared Parking model

"""

import logging
import argparse

from src import config

LOGGER = logging.getLogger("Shared Parking")


if __name__ == "__main__":

    step_names = ",".join(list(config.STEPS.keys()))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        "-c",
        dest="config",
        required=True,
        help="path to configuration file",
    )

    parser.add_argument(
        "--steps",
        "-s",
        nargs="+",
        dest="steps",
        metavar="STEPNAME",
        help=f"steps to run; omit to run all (choices: {step_names})",
    )

    args = parser.parse_args()

    configs = config.Config(args.config)
    configs.config_logger()

    configs.run(args.steps)
