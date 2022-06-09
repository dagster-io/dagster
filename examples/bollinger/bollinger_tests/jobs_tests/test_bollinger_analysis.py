from bollinger.assets.bollinger_analysis import (
    sp500_anomalous_events,
    sp500_bollinger_bands,
    sp500_prices,
)
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs.asset_selection import AssetSelection

from dagster.core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster.core.execution.with_resources import with_resources


def test_bollinger_analysis():
    bollinger_sda = define_asset_job(
        "test_job",
        AssetSelection.all(),
    ).resolve(
        with_resources(
            [sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
            {"io_manager": local_csv_io_manager},
        ),
        [],
    )
    result = bollinger_sda.execute_in_process()
    assert result.asset_materializations_for_node
