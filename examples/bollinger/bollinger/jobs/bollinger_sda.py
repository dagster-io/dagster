import pandas as pd
import pandera as pa
from bollinger.lib import compute_bollinger
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster import MEMOIZED_RUN_TAG
from dagster.core.asset_defs import asset, build_assets_job
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series


def get_sp500_prices_column_descriptions():
    return {
        "name": "Ticker symbol of stock",
        "date": "Date of prices",
        "open": "Price at market open",
        "high": "Highest price of the day",
        "low": "Lowest price of the day",
        "close": "Price at market close",
        "volume": "Number of shares traded for day",
    }


class Sp500Prices(pa.SchemaModel):
    name: Series[str] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    open: Series[float] = pa.Field(ge=0)
    high: Series[float] = pa.Field(ge=0)
    low: Series[float] = pa.Field(ge=0)
    close: Series[float] = pa.Field(ge=0)
    volume: Series[int] = pa.Field(ge=0)


@asset(
    dagster_type=pandera_schema_to_dagster_type(
        Sp500Prices, column_descriptions=get_sp500_prices_column_descriptions()
    ),
    metadata={"owner": "alice@example.com"},
    version="1",
)
def sp500_prices():
    """Historical stock prices for the S and P 500."""
    path = "examples/bollinger/data/all_stocks_5yr.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


def get_sp500_bollinger_bands_column_descriptions():
    return {
        "name": "Ticker symbol of stock",
        "date": "Date of prices",
        "upper": "Upper Bollinger band",
        "lower": "Lower Bollinger band",
    }


class Sp500BollingerBands(pa.SchemaModel):
    name: Series[str] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    upper: Series[float] = pa.Field()
    lower: Series[float] = pa.Field()


@asset(
    dagster_type=pandera_schema_to_dagster_type(
        Sp500BollingerBands, column_descriptions=get_sp500_bollinger_bands_column_descriptions()
    ),
    metadata={"owner": "alice@example.com"},
    version="2",
)
def sp500_bollinger_bands(sp500_prices):
    """Bollinger bands for the S and P 500 stock prices."""
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger(idf, dropna=False))
    return odf
    # return odf.dropna().reset_index()


def get_sp500_anomalous_events_column_descriptions():
    return {
        "date": "Date of event",
        "name": "Ticker symbol of stock",
        "event": "Type of event: 'high' or 'low'",
    }


class Sp500AnomalousEvents(pa.SchemaModel):
    date: Series[pd.Timestamp] = pa.Field()
    name: Series[str] = pa.Field()
    event: Series[pd.CategoricalDtype] = pa.Field()


@asset(
    dagster_type=pandera_schema_to_dagster_type(
        Sp500AnomalousEvents, column_descriptions=get_sp500_anomalous_events_column_descriptions()
    ),
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


bollinger_sda = build_assets_job(
    "bollinger_sda",
    assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
    resource_defs={"io_manager": local_csv_io_manager},
    tags={MEMOIZED_RUN_TAG: True},
)
