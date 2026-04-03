import dagster as dg

analytics_job = dg.define_asset_job("analytics_job", selection=["analytics"])


@dg.asset_sensor(asset_key=dg.AssetKey("daily_sales"), job=analytics_job)
def sales_sensor(context, asset_event):
    metadata = asset_event.dagster_event.event_specific_data.materialization.metadata
    row_count = metadata.get("row_count").value if "row_count" in metadata else 0
    if row_count > 1000:
        return dg.RunRequest()
    return dg.SkipReason(f"Row count {row_count} below threshold")
