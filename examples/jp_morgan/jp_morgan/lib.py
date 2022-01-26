from typing import cast
from pandera.typing.common import Int
from dagster import Field
from dagster.core.asset_defs import asset, build_assets_job

from dagster_pandera import pandera_schema_to_dagster_type

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series

from playground.util import resolve_data_path

# ****************************************************************************
# ***** TYPES ****************************************************************

class Sp500Prices(pa.SchemaModel):
    date: Series[pd.Timestamp] = pa.Field()
    open: Series[float] = pa.Field()
    high: Series[float] = pa.Field()
    low: Series[float] = pa.Field()
    close: Series[float] = pa.Field()
    volume: Series[int] = pa.Field()

Sp500PricesDgType = pandera_schema_to_dagster_type(Sp500Prices)

class Bollinger(pa.SchemaModel):
    name: Series[str] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    price: Series[float] = pa.Field()
    upper: Series[float] = pa.Field()
    lower: Series[float] = pa.Field()

BollingerDgType = pandera_schema_to_dagster_type(Bollinger)

# cat = pd.Categorical(['high', 'low'], ordered=False)

class AnomalousEvents(pa.SchemaModel):
    # date: Series[pd.PeriodDtype] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    name: Series[str] = pa.Field()
    type: Series[pd.CategoricalDtype] = pa.Field()

AnomalousEventsDgType = pandera_schema_to_dagster_type(AnomalousEvents)

# ****************************************************************************
# ***** FUNCTIONS ************************************************************

def load_sp500_prices() -> pd.DataFrame:
    path = resolve_data_path('all_stocks_5yr.csv')
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.rename(columns={'Name': 'name'})
    df = df.dropna()
    return df

def compute_bollinger(df: pd.DataFrame, rate: int = 30, sigma: float = 2.0, dropna=True) -> pd.DataFrame:
    price = df['close']
    rma = price.rolling(window=rate).mean()
    rstd = price.rolling(window=rate).std()
    upper = rma + sigma * rstd
    lower = rma - sigma * rstd
    odf = pd.DataFrame({'name': df['name'], 'date': df['date'], 'price': price, 'upper': upper, 'lower': lower})
    if dropna:
        odf = odf.dropna()
    return odf

def compute_bollinger_multi(df: pd.DataFrame, dropna: bool = True):
    odf = df.groupby('name').apply(lambda idf: compute_bollinger(idf, dropna=False))
    return odf.dropna().reset_index() if dropna else odf

def compute_anomalous_events(df: pd.DataFrame):
    idf = df[(df.price > df.upper) | (df.price < df.lower)].reset_index()
    idf['type'] = ((idf.price > idf.upper).astype('category').cat
        .rename_categories({True: 'high', False: 'low'}))
    return idf[['date', 'name', 'type']]