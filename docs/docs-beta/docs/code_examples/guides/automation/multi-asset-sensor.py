from dagster import (
    AssetKey,
    MultiAssetSensorEvaluationContext,
    RunRequest,
    asset,
    define_asset_job,
    multi_asset_sensor,
)


@asset
def target_asset():
    pass


downstream_job = define_asset_job("downstream_job", [target_asset])


@multi_asset_sensor(
    monitored_assets=[
        AssetKey("upstream_asset_1"),
        AssetKey("upstream_asset_2"),
    ],
    job=downstream_job,
)
def my_multi_asset_sensor(context: MultiAssetSensorEvaluationContext):
    run_requests = []
    for asset_key, materialization in context.latest_materialization_records_by_key().items():
        if materialization:
            run_requests.append(RunRequest(asset_selection=[asset_key]))
            context.advance_cursor({asset_key: materialization})
    return run_requests
