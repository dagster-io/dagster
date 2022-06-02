# pylint: disable=redefined-outer-name
from dagster import Field, asset

from ..lib import (
    AnomalousEventsDgType,
    BollingerBandsDgType,
    StockPricesDgType,
    compute_anomalous_events,
    compute_bollinger_bands_multi,
    load_sp500_prices,
)


@asset(
    dagster_type=StockPricesDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_prices():
    """Historical stock prices for the S&P 500."""
    return load_sp500_prices()


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
def sp500_bollinger_bands(context, sp500_prices):
    """Bollinger bands for the S&amp;P 500 stock prices."""
    return compute_bollinger_bands_multi(
        sp500_prices, rate=context.op_config["rate"], sigma=context.op_config["sigma"]
    )


@asset(
    dagster_type=AnomalousEventsDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_anomalous_events(sp500_prices, sp500_bollinger_bands):
    """Anomalous events for the S&P 500 stock prices."""
    return compute_anomalous_events(sp500_prices, sp500_bollinger_bands)
