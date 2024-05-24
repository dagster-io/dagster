from dagster import AssetKey, DagsterInstance
from docs_snippets.concepts.assets.external_assets.external_asset_events_using_python_api import (
    do_report_runless_asset_event,
)


def test_do_report_runless_asset_event() -> None:
    instance = DagsterInstance.ephemeral()
    do_report_runless_asset_event(instance)

    assert instance.get_latest_materialization_event(AssetKey("asset_one"))
