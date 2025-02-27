# Shared Parking Analysis Tool

[![Main Build](https://github.com/RSGInc/shared_parking/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/RSGInc/shared_parking/actions/workflows/main.yml)

## Quick start

1. Install `conda` via [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. Clone this repository and navigate to the project root directory
3. Run `conda env create -f environment.yml && conda activate shared_parking`
4. Run `python run_model.py -c tests/winooski_example/configuration.yaml` to use the example configuration

## Customization

1. Copy `tests/winooski_example` to a new directory and edit `configuration.yaml` to customize inputs and other parameters
2. Add an `-s` flag to the run command to specify individual steps, ex: `python run_model.py -c <your directory>/configuration.yaml -s factors preference`
3. Run `python run_model.py -h` for the full helptext

## Steps

Tool contains three model steps, run sequentially. Inputs and outputs for the Winooski scenario can be found in the `tests` directory. Timestamped logfiles are written to the `logs/` output subdirectory.

### Generate Parking Factors
Creates factors.csv, a csv of the factors dataframe. The factors dataframe contains every combination of factors related to shared parking.

**Inputs**
- Factors XLSX: `Parking Demand and Adjustments.xlsx`. Contains three sheets for Land Use, Monthly Usage, and TOD (time of day) factors

**Outputs**
- `factors.csv` a CSV of combined monthly, daily, and hourly demand factors

### Generate Parking Preference

This script takes a parking demand generator shapefile and a parking supply shapefile as input. The parking generators (demand) are joined to the nearest lots (supply) within a certain buffer distance. The joined file is saved to the outputs directory.

**Inputs**
- Demand Shapefile: `Winooski_Demand_Generators.shp`.
- Supply Shapefile: `Winooski_Parking_Supply.shp`.

**Outputs**
- Parking Preference CSV: `parking_preference.csv`.

### Generate Parking Demand

This script assigns demand from the generators, using the land use/time of day factors and parking preference lists to distribute parking among all of the lots for each time-slot defined in the factors file.

**Inputs**
- Factors DataFrame from `Generate Parking Factors`
- Parking Preference DataFrame from `Generate Parking Preference`

**Outputs**
- Parking Distribution: `timeseries.csv`.
