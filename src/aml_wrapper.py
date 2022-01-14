import argparse
import os
from azureml.core import Dataset, Run
from azureml.core.datastore import Datastore
from src.models.Config import Config
from src import process
from pathlib import Path

import subprocess
import sys

run = Run.get_context()
ws = run.experiment.workspace
config = Config.parse_file("config.json")

for package in config.pipeline.pip_packages:
    print("Installing " + package)
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', dest='output', required=True)
    return parser.parse_args()

args = parse_args()
print(f'Arguments: {args.__dict__}')


dfs = { ds_name: Dataset.get_by_name(ws, ds_name).to_pandas_dataframe() for ds_name in config.pipeline.input_datasets }

ret_dfs = process.run(dfs)

# os.makedirs(os.path.dirname(args.output), exist_ok=True)
# with open(args.output + "this_is_a_test_file.txt", 'w') as f:
#     f.write("Step 1's output")

# folder = os.path.dirname(args.output)
# os.makedirs(args.output, exist_ok=True)

# # with open(args.output, 'w') as f:
# #     f.write("Step 1's output")

# for key, value in ret_dfs.items():
#     path = args.output + "/" + key + ".parquet"
#     print(f"Saving data frame {key} to path {path}")
#     value.to_parquet(path)

p = Path(args.output)
p.mkdir(parents=True, exist_ok=True)

for key, value in ret_dfs.items():
    path = args.output + "/" + key + ".parquet"
    print(f"Saving data frame {key} to path {path}")
    value.to_parquet(path)