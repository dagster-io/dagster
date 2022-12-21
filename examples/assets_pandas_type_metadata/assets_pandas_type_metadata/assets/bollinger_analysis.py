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


from pydantic import Field
from dagster._config.structured_config import Config


class SP500BollingerBandsConfig(Config):
    rate: int = Field(30, description="Size of sliding window in days")
    sigma: float = Field(2.0, description="Width of envelop in standard deviations")


@asset(
    dagster_type=BollingerBandsDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_bollinger_bands(sp500_prices, config: SP500BollingerBandsConfig):
    """Bollinger bands for the S&amp;P 500 stock prices."""
    return compute_bollinger_bands_multi(sp500_prices, rate=config.rate, sigma=config.sigma)


@asset(
    dagster_type=AnomalousEventsDgType,
    metadata={"owner": "alice@example.com"},
)
def sp500_anomalous_events(sp500_prices, sp500_bollinger_bands):
    """Anomalous events for the S&P 500 stock prices."""
    return compute_anomalous_events(sp500_prices, sp500_bollinger_bands)
