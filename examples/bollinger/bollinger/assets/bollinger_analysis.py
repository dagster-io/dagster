# pylint: disable=redefined-outer-name
from dagster import Field, asset

from ..lib import (
    AnomalousEventsDgType,
    BollingerBandsDgType,
    StockPricesDgType,
    compute_anomalous_events,
    compute_bollinger_bands_multi,
    load_sp500_prices,
    download_file,
    SP500_CSV_URL,
    normalize_path,
)
import pandas as pd


@asset(
    dagster_type=StockPricesDgType,
    metadata={"owner": "alice@example.com"},
    io_manager_key="snowflake",
)
def sp500_prices(context):
    """Historical stock prices for the S&P 500."""
    df = load_sp500_prices()
    # df["date"] = df["date"].dt.tz_localize("US/Eastern")
    # df["date"] = df["date"].dt.ceil(freq='ms').values.astype("datetime64[ms]")
    # df["date"] = df["date"].apply(lambda x: pd.Timestamp(x))
    df["date"] = df["date"].dt.date
    context.log.info(f"date {df['date'][:10]}")
    context.log.info(f"sp500 prices head {df.head()}")
    context.log.info(f"data types {df.dtypes}")
    return df


# @asset(
#     dagster_type=StockPricesDgType,
#     metadata={"owner": "alice@example.com"},
#     io_manager_key="snowflake"
# )
# def sp500_prices() -> pd.DataFrame:
#     path = normalize_path("all_stocks_5yr.csv")
#     download_file(SP500_CSV_URL, path)
#     return load_sp500_prices()


@asset(
    dagster_type=BollingerBandsDgType,
    config_schema={
        "rate": Field(int, default_value=30, description="Size of sliding window in days"),
        "sigma": Field(
            float, default_value=2.0, description="Width of envelope in standard deviations"
        ),
    },
    metadata={"owner": "alice@example.com"},
)
def sp500_bollinger_bands(context, sp500_prices: pd.DataFrame):
    """Bollinger bands for the S&amp;P 500 stock prices."""
    return compute_bollinger_bands_multi(
        sp500_prices, rate=context.op_config["rate"], sigma=context.op_config["sigma"]
    )


@asset(
    dagster_type=AnomalousEventsDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_anomalous_events(sp500_prices: pd.DataFrame, sp500_bollinger_bands):
    """Anomalous events for the S&P 500 stock prices."""
    return compute_anomalous_events(sp500_prices, sp500_bollinger_bands)
