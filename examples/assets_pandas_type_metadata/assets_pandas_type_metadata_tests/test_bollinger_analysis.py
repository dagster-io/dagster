from dagster import AssetSelection, define_asset_job
from dagster._core.definitions.definitions_class import Definitions

from assets_pandas_type_metadata.assets.bollinger_analysis import (
    sp500_anomalous_events,
    sp500_bollinger_bands,
    sp500_prices,
)
from assets_pandas_type_metadata.resources.csv_io_manager import LocalCsvIOManager


def test_bollinger_analysis():
    bollinger_sda = define_asset_job(
        "bollinger_sda",
        AssetSelection.all(),
    )
    defs = Definitions(
        assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
        resources={
            "io_manager": LocalCsvIOManager(),
        },
        jobs=[bollinger_sda],
    )
    result = defs.get_job_def("bollinger_sda").execute_in_process()
    assert result.asset_materializations_for_node
