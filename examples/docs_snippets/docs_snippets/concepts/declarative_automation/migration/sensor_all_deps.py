import dagster as dg

downstream_job = dg.define_asset_job("downstream_job", selection=["downstream"])


@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
    job=downstream_job,
)
def all_deps_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return dg.RunRequest()
