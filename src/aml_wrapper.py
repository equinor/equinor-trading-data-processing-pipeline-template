# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# Install packages
# os.system(f"pip install yfinance")

# %%
import argparse
import pandas as pd
from azureml.core import Workspace, Datastore, Experiment, datastore
from azureml.core import Dataset, Run
from src.models.Config import Config
from src import process

import subprocess
import sys

# %%
run = Run.get_context()
ws = run.experiment.workspace
config = Config.parse_file("../src/config.json")

for package in config.pipeline.pip_packages:
    print("Installing " + package)
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', dest='output', required=True)
    return parser.parse_args()

args = parse_args()
print(f'Arguments: {args.__dict__}')

dfs = [Dataset.get_by_name(ws, ds_name).to_pandas_dataframe() for ds_name in config.pipeline.input_dataset]

process.run(dfs)