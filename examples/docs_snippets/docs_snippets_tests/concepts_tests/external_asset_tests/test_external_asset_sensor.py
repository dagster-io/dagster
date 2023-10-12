from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    SensorResult,
    build_sensor_context,
)
from docs_snippets.concepts.assets.external_assets.external_asset_using_sensor import (
    keep_external_asset_a_up_to_date,
)


def test_keep_external_asset_a_up_to_date() -> None:
    instance = DagsterInstance.ephemeral()
    result = keep_external_asset_a_up_to_date(
        build_sensor_context(
            instance=instance, sensor_name="keep_external_asset_a_up_to_date"
        )
    )
    assert isinstance(result, SensorResult)
    assert len(result.asset_events) == 1
    assert isinstance(result.asset_events[0], AssetMaterialization)
    assert result.asset_events[0].asset_key == AssetKey("external_asset_a")
