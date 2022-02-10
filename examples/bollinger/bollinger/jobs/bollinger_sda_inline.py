import os

import pandas as pd
import pandera as pa
from bollinger.lib import SP500_CSV_URL, download_file, normalize_path, compute_bollinger_bands
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster import MEMOIZED_RUN_TAG
from dagster.core.asset_defs import asset, build_assets_job
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series

# An inline version of the Bollinger Bands job, suitable for demos. Also elides the distinction
# between assets and types (types here are given names that map to specific assets). Types are not
# given descriptions since the assets themselves have descriptions. There are a few other minor
# differences as well from other bollinger_sda versions.


class Sp500Prices(pa.SchemaModel):
    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[pd.Timestamp] = pa.Field(description="Date of prices")
    open: Series[float] = pa.Field(ge=0, description="Price at market open")
    high: Series[float] = pa.Field(ge=0, description="Highest price of the day")
    low: Series[float] = pa.Field(ge=0, description="Lowest price of the day")
    close: Series[float] = pa.Field(ge=0, description="Price at market close")
    volume: Series[int] = pa.Field(ge=0, description="Number of shares traded for day")


@asset(
    dagster_type=pandera_schema_to_dagster_type(Sp500Prices),
    metadata={"owner": "alice@example.com"},
    version="1",
)
def sp500_prices():
    """Historical stock prices for the S and P 500."""
    path = normalize_path("all_stocks_5yr.csv")
    if not os.path.exists(path):
        download_file(SP500_CSV_URL, path)
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


class Sp500BollingerBands(pa.SchemaModel):
    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[pd.Timestamp] = pa.Field(description="Date of prices")
    upper: Series[float] = pa.Field(ge=0, description="Upper band")
    lower: Series[float] = pa.Field(description="Lower band")


@asset(
    dagster_type=pandera_schema_to_dagster_type(Sp500BollingerBands),
    metadata={"owner": "alice@example.com"},
    version="2",
)
def sp500_bollinger_bands(sp500_prices):
    """Bollinger bands for the S and P 500 stock prices."""
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger_bands(idf, dropna=False))
    return odf
    # return odf.dropna().reset_index()


class Sp500AnomalousEvents(pa.SchemaModel):
    date: Series[pd.Timestamp] = pa.Field(description="Date of price event")
    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    event: Series[pd.CategoricalDtype] = pa.Field(description="Type of event: 'high' or low'")


@asset(
    dagster_type=pandera_schema_to_dagster_type(Sp500AnomalousEvents),
    metadata={"owner": "alice@example.com"},
    version="1",
)
def sp500_anomalous_events(sp500_prices, sp500_bollinger_bands):
    """
    Anomalous price events, defined by a day on which a stock's closing price strayed above or below
    its Bollinger bands.
    """
    df = pd.concat([sp500_prices, sp500_bollinger_bands.add_prefix("bol_")], axis=1)
    df["event"] = pd.Series(
        pd.NA, index=df.index, dtype=pd.CategoricalDtype(categories=["high", "low"])
    )
    df["event"][df["close"] > df["bol_upper"]] = "high"
    df["event"][df["close"] < df["bol_lower"]] = "low"
    return df[df["event"].notna()][["name", "date", "event"]].reset_index()


bollinger_sda_inline = build_assets_job(
    "bollinger_sda",
    assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
    resource_defs={"io_manager": local_csv_io_manager},
    tags={MEMOIZED_RUN_TAG: True},
)
