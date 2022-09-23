import datetime
from dagster import asset, repository, source_asset, Field

from .lib import (
    BollingerBandsDgType,
    StockPricesDgType,
    compute_anomalous_events,
    compute_bollinger_bands_multi,
    load_sp500_prices,
)



@source_asset
def sp500_prices():
    return datetime.datetime.now()

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



@repository
def assets_reconciliation():
    return [
        sp500_prices,
        sp500_bollinger_bands
    ]
