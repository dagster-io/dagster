from dagster import In, Out, job, op

from ..lib import (
    AnomalousEventsDgType,
    BollingerDgType,
    Sp500PricesDgType,
    compute_anomalous_events,
    compute_bollinger_multi,
    load_sp500_prices,
)

# ****************************************************************************
# ***** OP VERSION ***********************************************************


@op(
    out=Out(dagster_type=Sp500PricesDgType),
)
def van_sp500_prices():
    return load_sp500_prices()


@op(
    ins={
        "sp500_prices": In(dagster_type=Sp500PricesDgType),
    },
    out=Out(dagster_type=BollingerDgType),
)
def van_bollinger(sp500_prices):
    return compute_bollinger_multi(sp500_prices)


@op(
    ins={
        "sp500_prices": In(dagster_type=Sp500PricesDgType),
        "bollinger": In(dagster_type=BollingerDgType),
    },
    out=Out(dagster_type=AnomalousEventsDgType),
)
def van_anomalous_events(sp500_prices, bollinger):
    return compute_anomalous_events(sp500_prices, bollinger)


@job
def bollinger_vanilla():
    prices = van_sp500_prices()
    van_anomalous_events(prices, van_bollinger(prices))
