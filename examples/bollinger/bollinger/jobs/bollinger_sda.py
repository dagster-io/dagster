import pandas as pd
import pandera as pa
from bollinger.lib import compute_bollinger
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs import asset, build_assets_job
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series


class Sp500Prices(pa.SchemaModel):
    name: Series[str] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    open: Series[float] = pa.Field(ge=0)
    high: Series[float] = pa.Field(ge=0)
    low: Series[float] = pa.Field(ge=0)
    close: Series[float] = pa.Field(ge=0)
    volume: Series[int] = pa.Field(ge=0)


Sp500PricesDgType = pandera_schema_to_dagster_type(
    Sp500Prices,
    description={
        "summary": "Historical stock prices for the S&P 500.",
        "columns": {
            "name": "Ticker symbol of stock",
            "date": "Date of prices",
            "open": "Price at market open",
            "high": "Highest price of the day",
            "low": "Lowest price of the day",
            "close": "Price at market close",
            "volume": "Number of shares traded for day",
        },
    },
)


class Bollinger(pa.SchemaModel):
    name: Series[str] = pa.Field()
    date: Series[pd.Timestamp] = pa.Field()
    price: Series[float] = pa.Field()
    upper: Series[float] = pa.Field()
    lower: Series[float] = pa.Field()


BollingerDgType = pandera_schema_to_dagster_type(
    Bollinger,
    description={
        "summary": "Bollinger bands for a set of stock prices.",
        "columns": {
            "name": "Ticker symbol of stock",
            "date": "Date of prices",
            "price": "Representative price for day",
            "upper": "Upper Bollinger band",
            "lower": "Lower Bollinger band",
        },
    },
)


class AnomalousEvents(pa.SchemaModel):
    date: Series[pd.Timestamp] = pa.Field()
    name: Series[str] = pa.Field()
    type: Series[pd.CategoricalDtype] = pa.Field()


AnomalousEventsDgType = pandera_schema_to_dagster_type(
    AnomalousEvents,
    description={
        "summary": """
        Anomalous price events, defined by a day on which a stock's price strayed above or below its
        Bollinger bands.
    """.replace(
            r"\n\s+", " "
        ),
        "columns": {
            "date": "Date of event",
            "name": "Ticker symbol of stock",
            "type": "Type of event: 'high' or 'low'",
        },
    },
)


@asset(dagster_type=Sp500PricesDgType)
def sp500_prices():
    path = "examples/bollinger/data/all_stocks_5yr.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


@asset(dagster_type=BollingerDgType)
def bollinger(sp500_prices):
    odf = sp500_prices.groupby("name").apply(lambda idf: compute_bollinger(idf, dropna=False))
    return odf


@asset(dagster_type=AnomalousEventsDgType)
def anomalous_events(bollinger):
    idf = bollinger[
        (bollinger.price > bollinger.upper) | (bollinger.price < bollinger.lower)
    ].reset_index()
    idf["type"] = (
        (idf.price > idf.upper)
        .astype("category")
        .cat.rename_categories({True: "high", False: "low"})
    )
    return idf[["date", "name", "type"]]


bollinger_sda = build_assets_job(
    "bollinger_sda",
    assets=[anomalous_events, bollinger, sp500_prices],
    resource_defs={"io_manager": local_csv_io_manager},
)
