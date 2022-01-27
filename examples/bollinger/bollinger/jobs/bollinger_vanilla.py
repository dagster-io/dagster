from dagster import In, Out, job, op
from ..lib import AnomalousEventsDgType, Sp500PricesDgType, load_sp500_prices, compute_bollinger_multi, compute_anomalous_events, BollingerDgType

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
    out=Out(dagster_type=BollingerDgType)
)
def van_bollinger(sp500_prices):
    return compute_bollinger_multi(sp500_prices)

@op(
    ins={
        "bollinger": In(dagster_type=BollingerDgType),
    },
    out=Out(dagster_type=AnomalousEventsDgType)
)
def van_anomalous_events(bollinger):
    return compute_anomalous_events(bollinger())
    
@job
def bollinger_vanilla():
    van_anomalous_events(van_bollinger(van_sp500_prices()))