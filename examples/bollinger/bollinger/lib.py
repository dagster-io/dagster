import pandas as pd
import pandera as pa
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series
from playground.util import resolve_data_path

# ****************************************************************************
# ***** TYPES ****************************************************************


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

# cat = pd.Categorical(['high', 'low'], ordered=False)


class AnomalousEvents(pa.SchemaModel):
    # date: Series[pd.PeriodDtype] = pa.Field()
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

# ****************************************************************************
# ***** FUNCTIONS ************************************************************


def load_sp500_prices() -> pd.DataFrame:
    path = resolve_data_path("all_stocks_5yr.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"Name": "name"})
    df = df.dropna()
    return df


def compute_bollinger(
    df: pd.DataFrame, rate: int = 30, sigma: float = 2.0, dropna=True
) -> pd.DataFrame:
    price = df["close"]
    rma = price.rolling(window=rate).mean()
    rstd = price.rolling(window=rate).std()
    upper = rma + sigma * rstd
    lower = rma - sigma * rstd
    odf = pd.DataFrame(
        {"name": df["name"], "date": df["date"], "price": price, "upper": upper, "lower": lower}
    )
    if dropna:
        odf = odf.dropna()
    return odf


def compute_bollinger_multi(df: pd.DataFrame, dropna: bool = True):
    odf = df.groupby("name").apply(lambda idf: compute_bollinger(idf, dropna=False))
    return odf.dropna().reset_index() if dropna else odf


def compute_anomalous_events(df: pd.DataFrame):
    idf = df[(df.price > df.upper) | (df.price < df.lower)].reset_index()
    idf["type"] = (
        (idf.price > idf.upper)
        .astype("category")
        .cat.rename_categories({True: "high", False: "low"})
    )
    return idf[["date", "name", "type"]]
