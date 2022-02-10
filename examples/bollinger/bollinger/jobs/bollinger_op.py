from dagster import In, Out, job, op

from ..lib import (
    AnomalousEventsDgType,
    BollingerBandsDgType,
    StockPricesDgType,
    compute_anomalous_events as _compute_anomalous_events,
    compute_bollinger_bands_multi as _compute_bollinger_bands_multi,
    load_sp500_prices as _load_sp500_prices,
)


@op(
    description=_load_sp500_prices.__doc__,
    out=Out(dagster_type=StockPricesDgType),
)
def load_sp500_prices():
    return _load_sp500_prices()


@op(
    description=_compute_bollinger_bands_multi.__doc__,
    ins={
        "prices": In(dagster_type=StockPricesDgType),
    },
    out=Out(dagster_type=BollingerBandsDgType),
)
def compute_bollinger_bands(prices):
    return _compute_bollinger_bands_multi(prices)


@op(
    ins={
        "prices": In(dagster_type=StockPricesDgType),
        "bollinger_bands": In(dagster_type=BollingerBandsDgType),
    },
    out=Out(dagster_type=AnomalousEventsDgType),
)
def compute_anomalous_events(prices, bollinger_bands):
    return _compute_anomalous_events(prices, bollinger_bands)

@job
def bollinger_op():
    prices = load_sp500_prices()
    compute_anomalous_events(prices, compute_bollinger_bands(prices))
