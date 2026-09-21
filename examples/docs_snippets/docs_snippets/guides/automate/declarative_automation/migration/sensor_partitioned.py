import dagster as dg


@dg.asset(partitions_def=dg.HourlyPartitionsDefinition("2024-01-01-00:00"))
def hourly_asset(): ...


@dg.asset(
    deps=["hourly_asset"],
    partitions_def=dg.WeeklyPartitionsDefinition(start_date="2024-01-01"),
)
def weekly_asset(): ...


weekly_job = dg.define_asset_job("weekly_job", selection=["weekly_asset"])


@dg.multi_asset_sensor(
    monitored_assets=[hourly_asset.key],
    job=weekly_job,
)
def hourly_to_weekly(context):
    for partition, record in context.latest_materialization_records_by_partition(
        hourly_asset.key
    ).items():
        mapped = context.get_downstream_partition_keys(
            partition,
            from_asset_key=hourly_asset.key,
            to_asset_key=weekly_asset.key,
        )
        for p in mapped:
            yield weekly_job.run_request_for_partition(partition_key=p)
        context.advance_cursor({hourly_asset.key: record})
