import dagster as dg


@dg.asset
def target_asset():
    pass


downstream_job = dg.define_asset_job("downstream_job", [target_asset])


@dg.multi_asset_sensor(
    monitored_assets=[
        dg.AssetKey("upstream_asset_1"),
        dg.AssetKey("upstream_asset_2"),
    ],
    job=downstream_job,
)
def my_multi_asset_sensor(context: dg.MultiAssetSensorEvaluationContext):
    run_requests = []
    for (
        asset_key,
        materialization,
    ) in context.latest_materialization_records_by_key().items():
        if materialization:
            run_requests.append(dg.RunRequest(asset_selection=[asset_key]))
            context.advance_cursor({asset_key: materialization})
    return run_requests
