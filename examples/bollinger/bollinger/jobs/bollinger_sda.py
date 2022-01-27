from pandera.typing.common import Int
from dagster import Field
from dagster.core.asset_defs import asset, build_assets_job

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series

from playground.util import resolve_data_path

from ..lib import AnomalousEventsDgType, BollingerDgType, Sp500PricesDgType, compute_bollinger_multi, load_sp500_prices, compute_bollinger, compute_anomalous_events

# ****************************************************************************
# ***** ASSET VERSION ********************************************************

@asset(dagster_type=Sp500PricesDgType)
def sp500_prices():
    return load_sp500_prices()

@asset(dagster_type=BollingerDgType)
def bollinger(sp500_prices):
    return compute_bollinger_multi(sp500_prices)

@asset(dagster_type=AnomalousEventsDgType)
def anomalous_events(bollinger):
    return compute_anomalous_events(bollinger)

bollinger_sda = build_assets_job('bollinger_sda', assets=[anomalous_events, bollinger, sp500_prices])