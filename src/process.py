from typing import Dict
import pandas as pd
import os

def run(args: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    iris_df = args["iris"]
    iris_df["test"] = "Hello world"
    print(iris_df)
    # The names of this dictionary will be the names of the output files
    return {
        "iris_data_processing_pipeline_template": iris_df
    }