# pylint: disable=redefined-outer-name
import pandas as pd

from dagster import Field, asset

from ..lib import (
    SP500_CSV_URL,
    AnomalousEventsDgType,
    BollingerBandsDgType,
    StockPricesDgType,
    compute_anomalous_events,
    compute_bollinger_bands_multi,
    download_file,
    load_sp500_prices,
    normalize_path,
)


@asset(
    dagster_type=StockPricesDgType,
    metadata={"owner": "alice@example.com"},
    io_manager_key="snowflake",
)
def sp500_prices():
    """Historical stock prices for the S&P 500."""
    df = load_sp500_prices()
    print("!!!!!!!!!!COLUMNS WITH NAN!!!!!!!!!!!!!!")
    print(df.columns[df.isna().any()].tolist())
    return df


# TODO - remove once download script works for me
# @asset(
#     dagster_type=StockPricesDgType,
#     metadata={"owner": "alice@example.com"},
#     io_manager_key="snowflake",
# )
# def sp500_prices_w_download() -> pd.DataFrame:
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
    context.log.info(f"sp500 head {sp500_prices.head()}")
    context.log.info(f"data types {sp500_prices.dtypes}")
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
