from bollinger.jobs.bollinger_sda import anomalous_events, bollinger, sp500_prices
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs import build_assets_job


def test_bollinger_sda():
    bollinger_sda = build_assets_job(
        "bollinger_sda",
        assets=[anomalous_events, bollinger, sp500_prices],
        resource_defs={"io_manager": local_csv_io_manager},
    )
    result = bollinger_sda.execute_in_process()
    result.asset_materializations_for_node
