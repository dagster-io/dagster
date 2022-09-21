from dagster import AssetKey, RunRequest, SensorDefinition, multi_asset_sensor


def make_hn_tables_updated_sensor(job) -> SensorDefinition:
    """
    Returns a sensor that launches the given job when the HN "comments" and "stories" tables have
    both been updated.
    """

    @multi_asset_sensor(
        asset_keys=[
            AssetKey(["snowflake", "core", "comments"]),
            AssetKey(["snowflake", "core", "stories"]),
        ],
        name=f"{job.name}_on_hn_tables_updated",
        job=job,
    )
    def hn_tables_updated_sensor(context):
        asset_events = context.latest_materialization_records_by_key()
        if all(asset_events.values()):
            context.advance_all_cursors()
            return RunRequest()

    return hn_tables_updated_sensor
