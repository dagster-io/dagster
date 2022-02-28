from bollinger.assets.bollinger_analysis import (
    sp500_anomalous_events,
    sp500_bollinger_bands,
    sp500_prices,
)
from bollinger.resources.csv_io_manager import local_csv_io_manager

from dagster import AssetGroup


def test_bollinger_analysis():
    bollinger_sda = AssetGroup(
        assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
        resource_defs={"io_manager": local_csv_io_manager},
    )
    result = bollinger_sda.build_job("test_job").execute_in_process()
    assert result.asset_materializations_for_node
