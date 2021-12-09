# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# imports up here can be used to
import pandas as pd
import numpy as np
# import os
# os.system(f"pip install yfinance")
import yfinance as yf

# The entry point function MUST have two input arguments.
# If the input port is not connected, the corresponding
# dataframe argument will be None.
#   Param<dataframe1>: a pandas.DataFrame
#   Param<dataframe2>: a pandas.DataFrame
def azureml_main(dataframe1 = None, dataframe2 = None):

    # import os
    # os.system(f"pip install yfinance")
    # import yfinance as yf

    ## Parameters
    PRICES = ["THE", "NCG", "TTF", "GASPOOL", "ZTP", "PEG"]
    MWH_PER_THERMS = 0.0293071
    PENCE_PER_POUND = 100

    # Execution logic goes here
    print(f'Input pandas.DataFrame #1: {dataframe1}')
    print("Code is changed!!!!")
    PRICES = ["THE", "NCG", "TTF", "GASPOOL", "ZTP", "PEG", "NBP"]
    THERMS_TO_MWH_UNIT_TRANSFORM = 1 / (MWH_PER_THERMS * PENCE_PER_POUND)

    ## Creating DF
    df_mapped = create_mapped_dataframe(dataframe1, dataframe2, PRICES)

    print("MAPPED DF: ")
    print(df_mapped.head(20))

    # Convert units NBP
    df_price_nbp_DA = convert_price_day_ahead(
        df_mapped, "NBP", "h", "GBPEUR=X", THERMS_TO_MWH_UNIT_TRANSFORM, True
    )
    print("NBP DA PRICE CONVERSION DONE:")
    print(df_price_nbp_DA.head(20))

    # Clean price_df
    df_price = create_dataframes_for_spreads_and_prices(
        df_mapped, PRICES
    )

    print("PRICE DF 1:")
    print(df_price.head(20))

    df_price = add_syntethic_data_to_dataframes(
        df_price,
        [df_price_nbp_DA]
    )

    print("FINAL PRICE DF:")
    print(df_price.head(20))

    # If a zip file is connected to the third input port,
    # it is unzipped under "./Script Bundle". This directory is added
    # to sys.path. Therefore, if your zip file contains a Python file
    # mymodule.py you can import it using:
    # import mymodule

    # Return value must be of a sequence of pandas.DataFrame
    # E.g.
    #   -  Single return value: return dataframe1,
    #   -  Two return values: return dataframe1, dataframe2
    return df_price

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

    df_mapped = df_mapped[df_mapped["FirstSequenceItemName"] == "DA"]

    df = df_mapped[
        [
            "Price",
            "Volume",
            # "Unit",
            "FirstSequenceItemName",
            "SecondSequenceItemName",
            "Instrument Group",
        ]
    ]

    return df

def convert_price_day_ahead(
    df: pd.DataFrame,
    instrument_group: str,
    interval: str,
    currency_tickers: str,
    unit_transform: float = 1.0,
    remove_time_spread: bool = False,
) -> pd.DataFrame:
    """
    Filter dataframe for day ahead on instrument_group and convert 'close' price to a different currency, also scaling for
    different units in different markets (e.g. NBP uses pence per therm, TTF uses €/MWh)
    :param df: dataframe with price data in 'close'
    :param instrument_group: instrument group to get, e.g. 'NBP'
    :param interval: frequency of data, e.g. every hour ('H') or once a day ('D'), same concept as pandas 'resample'
    :param currency_tickers: currency using yfinance notation, e.g. 'GBPEUR=X' is GBP to EURO
    :param unit_transform: multiplication factor to convert price to standard currency unit per MWh common units (e.g. from pence per therm to GBP/MWh)
    :param remove_time_spread: True means remove time spread, i.e. all values where SecondSequenceItemName is NaN
    :return: filtered dataframe, with values converted to target currency / measurement units
    """

    price_df = _create_price_df(
        df, instrument_group, ["DA"], interval, remove_time_spread
    )
    price_df["close"] = convert_currency(
        price_df["close"], tickers=currency_tickers, period="730d", interval="1h"
    )

    price_df["close"] = price_df["close"] * unit_transform
    return price_df

def _create_price_df(
    df: pd.DataFrame,
    instrument_group: str,
    contract_types: list,
    interval: str,
    remove_time_spread: bool,
):
    """
    :param df: dataframe with price data
    :param instrument_group: instrument group of interest
    :param contract_types: list of contracts of interest
    :param interval: frequency of data, e.g. every hour ('H') or once a day ('D'), same concept as pandas 'resample'
    :param remove_time_spread: remove time spread if True (remove values where SecondSequenceItemName is NaN)
    :return: dataframe with relevant price data
    """
    price_df = _get_instrument_and_period(df, instrument_group, contract_types)
    if remove_time_spread:
        price_df = price_df[price_df["SecondSequenceItemName"].isna()]
    group = price_df.groupby(["FirstSequenceItemName", "Instrument Group"])
    price_df = (
        group["Price"].resample(interval).ohlc().reset_index().set_index("DateTime")
    )
    return price_df

def _get_instrument_and_period(
    df: pd.DataFrame, instrument_group: str, contract_types: list
):
    """
    :param df: dataframe with price data (all instrument groups)
    :param instrument_group: instrument group of interest
    :param contract_types: list of contracts of interest
    :return: dataframe with data only for given instrument group and contract types
    """
    instrument_group = [instrument_group]
    df = df[df["Instrument Group"].isin(instrument_group)]
    periods = _get_contract_types(df, contract_types)
    df = df[df["FirstSequenceItemName"].isin(periods)]
    return df

def _get_contract_types(df: pd.DataFrame, contract_types: list):
    """
    :param df: dataframe with relevant data
    :param contract_types: list of contracts of interest
    :return: list of relevant contract types found in df
    """
    if type(contract_types) is str:
        contract_types = [contract_types]

    all_contract_types = df["FirstSequenceItemName"].dropna().unique()
    all_contract_types = [x for x in all_contract_types if x is not None]
    wanted_contract_types = []
    for contract in all_contract_types:
        if contract[0:3] in contract_types or contract[0] in contract_types:
            wanted_contract_types.append(contract)
    return wanted_contract_types

def convert_currency(
    price: pd.Series, tickers: str, period: str, interval: str
) -> pd.Series:
    """
    Converts the a price series to another currency using the spot FX rate
    :param price: price data
    :param tickers: currency using yfinance notation, e.g. GBPEUR=X is GBP to EURO
    :param period: number e.g. days of interest, counting from now, max period is 730 days if interval is hours
    :param interval: interval that the currency should be converted, 1h is one hour
    :return: price column where currency conversion has been applied
    """
    currency_data = _fetch_spot_rate_curve(tickers, period, interval)
    price, currency_data = get_df_with_available_data(price, currency_data)

    return price * currency_data["Close"]   

def _fetch_spot_rate_curve(tickers: str, period: str, interval: str):
    """
    :param tickers: currency using yfinance notation, e.g. GBPEUR=X is GBP to EURO
    :param period: number e.g. days of interest, counting from now, max period is 730 days if interval is hours
    :param interval: interval that the currency should be converted, 1h is one hour
    :return: currency spot rate series
    """
    currency_data_all = yf.download(tickers=tickers, period=period, interval=interval)
    currency_data_all.index = currency_data_all.index.tz_convert("UTC")

    return currency_data_all

def get_df_with_available_data(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    :param df_big: dataframe 1
    :param df_small: dataframe 2
    :return: both input dataframes with the same index values
    """
    df2 = df2.loc[df2.index.isin(df1.index)]
    df1 = df1.loc[df1.index.isin(df2.index)]

    return df1, df2

def add_syntethic_data_to_dataframes(
    df_price: pd.DataFrame,
    synthetic_price: list,
):
    """
    :param df_price: dataframe with price data
    :param synthetic_price: list of dataframes with syntehtic prices
    """
    for price in synthetic_price:
        price = price[["close", "FirstSequenceItemName", "Instrument Group"]]
        df_price = df_price.append(price)

    return df_price

def create_dataframes_for_spreads_and_prices(
    df: pd.DataFrame, prices: list
):
    """
    :param df: mapped dataframe with selected instruments and features
    :param price: list of instrument groups we want to keep
    :return: dataframes containing spread data and price data
    """
    df_price = df[df["Instrument Group"].isin(prices)]
    group = df_price.groupby(["FirstSequenceItemName", "Instrument Group"])
    result = group["Price"].resample("D").ohlc().reset_index().set_index("DateTime")
    df_price = result[["close", "FirstSequenceItemName", "Instrument Group"]].dropna()

    return df_price
