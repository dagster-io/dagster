import os
from typing import cast

import matplotlib.pyplot as plt
import pandas as pd
import pandera as pa
import requests
import seaborn as sns
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series

# ****************************************************************************
# ***** TYPES ****************************************************************


class StockPrices(pa.SchemaModel):
    """Open/high/low/close prices for a set of stocks by day."""

    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[pd.Timestamp] = pa.Field(description="Date of prices")
    open: Series[float] = pa.Field(ge=0, description="Price at market open")
    high: Series[float] = pa.Field(ge=0, description="Highest price of the day")
    low: Series[float] = pa.Field(ge=0, description="Lowest price of the day")
    close: Series[float] = pa.Field(ge=0, description="Price at market close")
    volume: Series[int] = pa.Field(ge=0, description="Number of shares traded for day")


StockPricesDgType = pandera_schema_to_dagster_type(StockPrices)


class BollingerBands(pa.SchemaModel):
    """Bollinger bands for a set of stock prices."""

    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[pd.Timestamp] = pa.Field(description="Date of prices")
    upper: Series[float] = pa.Field(ge=0, description="Upper band")
    lower: Series[float] = pa.Field(description="Lower band")


BollingerBandsDgType = pandera_schema_to_dagster_type(BollingerBands)


class AnomalousEvents(pa.SchemaModel):
    """Anomalous price events, defined by a day on which a stock's closing price strayed above or
    below its Bollinger bands."""

    date: Series[pd.Timestamp] = pa.Field(description="Date of price event")
    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    event: Series[pd.CategoricalDtype] = pa.Field(description="Type of event: 'high' or low'")


AnomalousEventsDgType = pandera_schema_to_dagster_type(AnomalousEvents)

# ****************************************************************************
# ***** FUNCTIONS ************************************************************

DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
SP500_CSV_URL = "https://raw.githubusercontent.com/plotly/datasets/master/all_stocks_5yr.csv"


def normalize_path(path: str) -> str:
    return path if path[0] == "/" else os.path.join(DATA_ROOT, path)


def download_file(url: str, path: str):
    """Download a file from a URL to a local path. If relative path, will be resolved relative to `DATA_ROOT`."""
    path = normalize_path(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(requests.get(url).content)


def load_prices_csv(path: str) -> pd.DataFrame:
    """Load a CSV file containing stock prices. CSV should conform to the schema in the
    `StockPrices` pandera schema above. If relative path, will be resolved relative to
    `DATA_ROOT`."""
    path = normalize_path(path)
    df = cast(pd.DataFrame, pd.read_csv(path, parse_dates=["date"]))
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


def load_sp500_prices(download: bool = True) -> pd.DataFrame:
    path = normalize_path("all_stocks_5yr.csv")
    if not os.path.exists(path):
        if download:
            download_file(SP500_CSV_URL, path)
        else:
            raise FileNotFoundError(f"{path} not found")
    return load_prices_csv(path)


def compute_bollinger_bands(
    df: pd.DataFrame, rate: int = 30, sigma: float = 2.0, dropna=True
) -> pd.DataFrame:
    """Compute Bollinger bands for a single stock over time. The dataframe passed in here should be
    represent a single timeseries."""
    price = df["close"]
    rma = price.rolling(window=rate).mean()
    rstd = price.rolling(window=rate).std()
    upper = rma + sigma * rstd
    lower = rma - sigma * rstd
    odf = pd.DataFrame({"name": df["name"], "date": df["date"], "upper": upper, "lower": lower})
    if dropna:
        odf = odf.dropna()
    return odf


def compute_bollinger_bands_multi(df: pd.DataFrame, dropna: bool = True):
    """Compute Bollinger bands for a set of stocks over time. The input dataframe can contain
    multiple timeseries grouped by the `name` column."""
    odf = df.groupby("name").apply(lambda idf: compute_bollinger_bands(idf, dropna=False))
    return odf.dropna().reset_index() if dropna else odf


EVENT_TYPE = pd.CategoricalDtype(["high", "low"], ordered=False)


def compute_anomalous_events(df_prices: pd.DataFrame, df_bollinger: pd.DataFrame):
    """Compute anomalous (high or low) price events for a set of stocks over time."""
    df = pd.concat([df_prices, df_bollinger.add_prefix("bol_")], axis=1)
    df["event"] = pd.Series(pd.NA, index=df.index, dtype=EVENT_TYPE)
    df["event"][df["close"] > df["bol_upper"]] = "high"  # type: ignore
    df["event"][df["close"] < df["bol_lower"]] = "low"  # type: ignore
    return df[df["event"].notna()][["name", "date", "event"]].reset_index()


# ****************************************************************************
# ***** VISUALIZATIONS *******************************************************


def plot_sample_bollinger_bands(df_prices, df_bollinger):
    df = pd.concat([df_prices, df_bollinger.add_prefix("bol_")], axis=1)
    plt.figure(figsize=(16, 30))
    for i, n in enumerate(df["name"].unique()[:5]):
        bdf = df[df["name"] == n]
        plt.subplot(5, 1, i + 1)
        plt.title(n)
        plt.plot(bdf["close"])
        plt.plot(bdf["bol_upper"])
        plt.plot(bdf["bol_lower"])


def plot_sample_anonymous_events(df_anom):
    top_20 = df_anom.groupby("name").size().sort_values(ascending=False)[:20].index.to_list()
    plt.figure(figsize=(16, 6))
    df = df_anom[df_anom.name.isin(top_20)]
    sns.stripplot(x="name", y="date", data=df, hue="event")
