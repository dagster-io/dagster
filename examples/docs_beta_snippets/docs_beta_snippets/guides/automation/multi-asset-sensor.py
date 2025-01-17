import dagster as dg


@dg.asset
def asset_a():
    return [1, 2, 3]


@dg.asset
def asset_b():
    return [5, 6, 7]


@dg.asset
def asset_c():
    return [8, 9, 10]


asset_job = dg.define_asset_job(
    "asset_b_job",
    selection=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b"), dg.AssetKey("asset_c")],
)


@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
    job=asset_job,
)
def asset_a_and_b_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return dg.RunRequest(run_key=context.cursor, run_config={})
    return None


defs = dg.Definitions(
    assets=[asset_a, asset_b, asset_c], jobs=[asset_job], sensors=[asset_a_and_b_sensor]
)
