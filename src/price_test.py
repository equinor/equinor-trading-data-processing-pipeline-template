# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# imports up here can be used to
import pandas as pd
import numpy as np



# The entry point function MUST have two input arguments.
# If the input port is not connected, the corresponding
# dataframe argument will be None.
#   Param<dataframe1>: a pandas.DataFrame
#   Param<dataframe2>: a pandas.DataFrame
def azureml_main(dataframe1 = None, dataframe2 = None):

    import os
    os.system(f"pip install yfinance")
    import yfinance as yf

    # Execution logic goes here
    print(f'Input pandas.DataFrame #1: {dataframe1}')
    print("Code is changed!!!!")
    PRICES = ["THE", "NCG", "TTF", "GASPOOL", "ZTP", "PEG", "NBP"]

    df_mapped = create_mapped_dataframe(dataframe1, dataframe2, PRICES)

    print(df_mapped.head(20))

    # If a zip file is connected to the third input port,
    # it is unzipped under "./Script Bundle". This directory is added
    # to sys.path. Therefore, if your zip file contains a Python file
    # mymodule.py you can import it using:
    # import mymodule

    # Return value must be of a sequence of pandas.DataFrame
    # E.g.
    #   -  Single return value: return dataframe1,
    #   -  Two return values: return dataframe1, dataframe2
    return dataframe1,

def create_mapped_dataframe(
    df: pd.DataFrame, df_instruments: pd.DataFrame, prices: list):
    """
    :param df: dataframe containing data from trayport
    :param df_instruments: dataframe contianing relevant instruments
    :return: dataframe of mapping between df and df_instruments
    """
    print("Creating df with selected instruments and features")

    # instruments = prices + spreads + ["NBP"]
    df_instruments_ = df_instruments[
        df_instruments["Instrument Group"].isin(prices)
    ]

    df_mapped = pd.merge(
        df, df_instruments_, left_on="InstName", right_on="Instrument"
    ).set_index("DateTime")

    df_mapped.index = df_mapped.index.tz_localize("CET", ambiguous=True).tz_convert(
        "UTC"
    )

    df = df_mapped[
        [
            "Price",
            "Volume",
            "Unit",
            "FirstSequenceItemName",
            "SecondSequenceItemName",
            "Instrument Group",
        ]
    ]

    return df
