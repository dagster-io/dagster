import dagster as dg

downstream_job = dg.define_asset_job("downstream_job", selection=["downstream"])


@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("important_source")],
    job=downstream_job,
)
def selective_sensor(context):
    events = context.latest_materialization_records_by_key()
    if events.get(dg.AssetKey("important_source")):
        context.advance_all_cursors()
        return dg.RunRequest()
