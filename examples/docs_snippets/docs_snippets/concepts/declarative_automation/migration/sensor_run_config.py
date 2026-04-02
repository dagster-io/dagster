import dagster as dg

processing_job = dg.define_asset_job("processing_job", selection=["processed_data"])


@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("raw_data")],
    job=processing_job,
)
def config_sensor(context):
    events = context.latest_materialization_records_by_key()
    record = events.get(dg.AssetKey("raw_data"))
    if record:
        metadata = record.asset_materialization.metadata
        file_path = metadata["file_path"].value
        context.advance_all_cursors()
        return dg.RunRequest(
            run_config={"ops": {"process": {"config": {"file_path": file_path}}}}
        )
