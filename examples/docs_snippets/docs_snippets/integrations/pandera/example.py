import random

import pandas as pd
import pandera as pa
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.typing import Series

from dagster import Out, job, op

APPLE_STOCK_PRICES = {
    "name": ["AAPL", "AAPL", "AAPL", "AAPL", "AAPL"],
    "date": ["2018-01-22", "2018-01-23", "2018-01-24", "2018-01-25", "2018-01-26"],
    "open": [177.3, 177.3, 177.25, 174.50, 172.0],
    "close": [177.0, 177.04, 174.22, 171.11, 171.51],
}


class StockPrices(pa.SchemaModel):
    """Open/close prices for one or more stocks by day."""

    name: Series[str] = pa.Field(description="Ticker symbol of stock")
    date: Series[str] = pa.Field(description="Date of prices")
    open: Series[float] = pa.Field(ge=0, description="Price at market open")
    close: Series[float] = pa.Field(ge=0, description="Price at market close")


@op(out=Out(dagster_type=pandera_schema_to_dagster_type(StockPrices)))
def apple_stock_prices_dirty():
    prices = pd.DataFrame(APPLE_STOCK_PRICES)
    i = random.choice(prices.index)
    prices.loc[i, "open"] = pd.NA
    prices.loc[i, "close"] = pd.NA
    return prices


@job
def stocks_job():
    apple_stock_prices_dirty()
