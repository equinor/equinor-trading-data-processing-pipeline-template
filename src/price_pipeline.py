# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# imports up here can be used to
import pandas as pd
import numpy as np
# import os
# os.system(f"pip install yfinance")
import yfinance as yf
from datetime import datetime

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
    PRICES = ["THE", "NCG", "TTF", "GASPOOL", "ZTP", "PEG", "NBP"]
    MWH_PER_THERMS = 0.0293071
    PENCE_PER_POUND = 100
    THERMS_TO_MWH_UNIT_TRANSFORM = 1 / (MWH_PER_THERMS * PENCE_PER_POUND)

    ## Creating DF
    df_mapped = create_mapped_dataframe(dataframe1, dataframe2, PRICES)

    # Convert units NBP
    df_price_nbp_DA = convert_price_day_ahead(
        df_mapped, "NBP", "1d", "GBPEUR=X", THERMS_TO_MWH_UNIT_TRANSFORM
    )
    # Join converted NBP prices with full price_df
    df_price = join_nbp_converted(
        df_mapped, df_price_nbp_DA
    )

    return df_price

def join_nbp_converted(
        df_mapped: pd.DataFrame, df_price_nbp_DA: pd.DataFrame
    ):
    # filter out unconverted NBP data
    df_mapped = df_mapped[df_mapped["Instrument Group"]!="NBP"].reset_index()

    # Concat both DFs and set DateTime as index, then order by DateTime
    joined_df = pd.concat([df_mapped,df_price_nbp_DA.reset_index()])
    joined_df = joined_df[joined_df["DateTime"] >= "2019-01-01"]
    joined_df.set_index("DateTime").sort_values("DateTime")

    return joined_df
    

def create_mapped_dataframe(
    df: pd.DataFrame, df_instruments: pd.DataFrame, prices: list):
    """
    :param df: dataframe containing data from trayport
    :param df_instruments: dataframe contianing relevant instruments
    :return: dataframe of mapping between df and df_instruments, resampled for daily granularity
    """
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
    # Filter for DA 
    df_mapped = df_mapped[df_mapped["FirstSequenceItemName"] == "DA"]

    df = df_mapped[
        [
            "Price",
            "FirstSequenceItemName",
            "Instrument Group",
        ]
    ]

    # Resample data to get daily close price
    df = resample_df(df)
    df = df[[
        "close",
        "FirstSequenceItemName",
        "Instrument Group"
    ]].dropna()

    return df

def resample_df(df: pd.DataFrame):
    group = df.groupby(["FirstSequenceItemName", "Instrument Group"])
    resampled_df = (
        group["Price"].resample("D").ohlc().reset_index().set_index("DateTime")
    )

    return resampled_df

def convert_price_day_ahead(
    df: pd.DataFrame,
    instrument_group: str,
    interval: str,
    currency_tickers: str,
    unit_transform: float = 1.0,
) -> pd.DataFrame:
    """
    Filter dataframe for day ahead on instrument_group and convert 'close' price to a different currency, also scaling for
    different units in different markets (e.g. NBP uses pence per therm, TTF uses €/MWh)
    :param df: dataframe with price data in 'close'
    :param instrument_group: instrument group to get, e.g. 'NBP'
    :param interval: frequency of data, e.g. every hour ('H') or once a day ('D'), same concept as pandas 'resample'
    :param currency_tickers: currency using yfinance notation, e.g. 'GBPEUR=X' is GBP to EURO
    :param unit_transform: multiplication factor to convert price to standard currency unit per MWh common units (e.g. from pence per therm to GBP/MWh)
     :return: filtered dataframe, with values converted to target currency / measurement units
    """
    # Filter df for unit conversion
    price_df = df[df["Instrument Group"] == instrument_group]

    # Set API call parameters
    period = get_period()

    # Convert currency
    price_df["close"] = convert_currency(
        price_df["close"], tickers=currency_tickers, period=period, interval=interval
    )

    price_df["close"] = price_df["close"] * unit_transform
    price_df.dropna(inplace=True)
    return price_df

def get_period():
    # Current time
    current_date = datetime.now()
  
    # Start date
    start_date = datetime(2019,1,1,0,0,0)

    # Timedelta in days is the period for the API
    period = str((current_date - start_date).days)+"d"

    return period

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
    currency_data_all.index = currency_data_all.index.tz_localize("UTC")

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

