import dagster as dg


@dg.asset
def target_asset():
    pass


# Job to trigger
downstream_job = dg.define_asset_job("downstream_job", [target_asset])


# highlight-start
# Sensor monitoring multiple assets
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
        # Trigger downstream_job when any of the monitored assets are materialized
        if materialization:
            run_requests.append(dg.RunRequest(asset_selection=[asset_key]))
            context.advance_cursor({asset_key: materialization})
    return run_requests
    # highlight-end
