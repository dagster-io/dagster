from bollinger.jobs.bollinger_analysis import sp500_prices, sp500_anomalous_events, sp500_bollinger_bands
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster.core.asset_defs import build_assets_job


def test_bollinger_analysis():
    bollinger_sda = build_assets_job(
        "bollinger_sda",
        assets=[sp500_anomalous_events, sp500_bollinger_bands, sp500_prices],
        resource_defs={"io_manager": local_csv_io_manager},
    )
    result = bollinger_sda.execute_in_process()
    assert result.asset_materializations_for_node
