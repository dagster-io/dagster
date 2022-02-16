# pylint: disable=redefined-outer-name
from dagster import asset, build_assets_job

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
    metadata={"owner": "alice@example.com"},
)
def sp500_bollinger_bands(sp500_prices):
    """Bollinger bands for the S&amp;P 500 stock prices."""
    return compute_bollinger_bands_multi(sp500_prices)


@asset(
    dagster_type=AnomalousEventsDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_anomalous_events(sp500_prices, sp500_bollinger_bands):
    """Anomalous events for the S&P 500 stock prices."""
    return compute_anomalous_events(sp500_prices, sp500_bollinger_bands)


bollinger_analysis = build_assets_job(
    "bollinger_analysis",
    assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
)
