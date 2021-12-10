import pandas as pd
import numpy as np

from price_pipeline import azureml_main

df1 = pd.read_parquet(r"C:\Appl\my_code\equinor-trading-data-processing-pipeline-template\data\trayport-trades-light.parquet")
df2 = pd.read_csv(r"C:\Appl\my_code\equinor-trading-data-processing-pipeline-template\data\instruments.csv")

# print(df1.head())
# print(df2.head())

df_price = azureml_main(df1,df2)

print(df_price.head())