import os
import sys
import time
import yaml
import logging

import pandas as pd
import geopandas as gpd

from . import (
    generate_factors,
    generate_preference,
    generate_demand,
)

STEPS = {
    "factors": generate_factors,
    "preference": generate_preference,
    "demand": generate_demand,
}

LOGGER = logging.getLogger("Shared Parking")


class Config:
    def __init__(self, config_file):

        self.config_file = config_file

        # read configs from yaml file
        with open(self.config_file) as file:
            self.configs = yaml.safe_load(file)

        self.data_dir = self.set_data_dir()
        self.output_dir = self.set_output_dir()

    def set_data_dir(self):

        data_dir = self.configs["data_dir"]

        if os.path.isdir(data_dir):

            return data_dir

        base_dir = os.path.dirname(self.config_file)
        data_path = os.path.join(base_dir, data_dir)

        if os.path.isdir(data_path):

            return data_path

        raise FileNotFoundError(f"Could not find data directory {data_dir}")

    def set_output_dir(self):

        output_dir = self.configs["output_dir"]

        if os.path.isdir(output_dir):

            return output_dir

        base_dir = os.path.dirname(self.config_file)
        output_path = os.path.join(base_dir, output_dir)

        os.makedirs(output_path, exist_ok=True)

        return output_path

    def config_logger(self, logfile_directory="logs"):

        logfile_directory = self.output_path(logfile_directory)

        if not os.path.exists(logfile_directory):
            os.mkdir(logfile_directory)

        # console handler
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s - %(message)s")
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)

        # file handler
        logfile = f"shared_parking_{time.strftime('%Y%b%d_%H_%M_%S_%p')}.log"
        fh = logging.FileHandler(os.path.join(logfile_directory, logfile))
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)

        logging.captureWarnings(True)

        kwargs = {
            "level": logging.DEBUG,
            "handlers": [ch, fh],
        }

        if sys.version_info.minor >= 8:
            kwargs["force"] = True

        logging.basicConfig(**kwargs)

        # silence fiona
        fiona_logger = logging.getLogger("fiona")
        fiona_logger.setLevel(logging.ERROR)

        LOGGER.info(f"saving verbose logs to {logfile}")

    def get(self, item):

        if item not in self.configs:
            LOGGER.warning(f"{item} not found in {self.config_file}")
            return

        return self.configs[item]

    def dump(self):

        return "\n" + yaml.dump(self.configs)

    def data_path(self, filename):

        return os.path.join(self.data_dir, filename)

    def output_path(self, filename):

        return os.path.join(self.output_dir, filename)

    def read_excel_sheet(self, filename, sheetname):

        filepath = self.data_path(filename)

        assert sheetname is not None

        return pd.read_excel(filepath, sheetname, engine="openpyxl")

    def read_shapefile(self, filename):

        filepath = self.data_path(filename)

        return gpd.read_file(filepath)

    def write_dataframe(self, df, filename):

        filepath = self.output_path(filename)
        df.to_csv(filepath, index=False)

        LOGGER.info(f"{len(df)} lines written to {filepath}")

    def read_input_dataframe(self, filename):

        filepath = self.data_path(filename)

        return pd.read_csv(filepath)

    def read_output_dataframe(self, filename):

        filepath = self.output_path(filename)

        return pd.read_csv(filepath)

    def run(self, step_list):

        # run all steps if none given
        if not step_list:

            for module in STEPS.values():
                module.run(self)

            return

        for step in step_list:

            assert step in STEPS, f"'{step}' is not a valid step name"

        for step, module in STEPS.items():

            # do it this way to ensure steps are in order
            if step in step_list:
                module.run(self)
