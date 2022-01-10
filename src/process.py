from typing import List
import pandas as pd
import os

def run(args: List[pd.DataFrame]) -> List[pd.DataFrame]:
    df = args[0]
    df["test"] = "Hello world"
    print(df)
    return [df]