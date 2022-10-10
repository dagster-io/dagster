from dagster import (
    AssetKey,
    AssetSelection,
    DailyPartitionsDefinition,
    RunRequest,
    SkipReason,
    WeeklyPartitionsDefinition,
    asset,
    asset_sensor,
    define_asset_job,
    job,
    multi_asset_sensor,
)


@job
def my_job():
    pass


# start_asset_sensor_marker
from dagster import AssetKey, EventLogEntry, SensorEvaluationContext, asset_sensor


@asset_sensor(asset_key=AssetKey("my_table"), job=my_job)
def my_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(
        run_key=context.cursor,
        run_config={
            "ops": {
                "read_materialization": {
                    "config": {
                        "asset_key": asset_event.dagster_event.asset_key.path,
                    }
                }
            }
        },
    )


# end_asset_sensor_marker


# start_multi_asset_sensor_marker


@multi_asset_sensor(
    asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
    job=my_job,
)
def asset_a_and_b_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest()


# end_multi_asset_sensor_marker

# start_multi_asset_sensor_w_skip_reason


@multi_asset_sensor(
    asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
    job=my_job,
)
def asset_a_and_b_sensor_with_skip_reason(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest()
    elif any(asset_events.values()):
        materialized_asset_key_strs = [
            key.to_user_string() for key, value in asset_events.items() if value
        ]
        not_materialized_asset_key_strs = [
            key.to_user_string() for key, value in asset_events.items() if not value
        ]
        return SkipReason(
            f"Observed materializations for {materialized_asset_key_strs}, "
            f"but not for {not_materialized_asset_key_strs}"
        )


# end_multi_asset_sensor_w_skip_reason


daily_partitions_def = DailyPartitionsDefinition(start_date="2022-08-01")


@asset(partitions_def=daily_partitions_def)
def downstream_daily_asset():
    return 1


downstream_daily_job = define_asset_job(
    "downstream_daily_job",
    AssetSelection.keys("downstream_daily_asset"),
    partitions_def=daily_partitions_def,
)

weekly_partitions_def = WeeklyPartitionsDefinition(start_date="2022-08-01")


@asset(partitions_def=weekly_partitions_def)
def downstream_weekly_asset():
    return 1


weekly_asset_job = define_asset_job(
    "weekly_asset_job",
    AssetSelection.keys("downstream_weekly_asset"),
    partitions_def=weekly_partitions_def,
)

# start_daily_asset_to_weekly_asset


@multi_asset_sensor(asset_keys=[AssetKey("upstream_daily_asset")], job=weekly_asset_job)
def trigger_weekly_asset_from_daily_asset(context):
    run_requests = []
    materializations_by_partition = context.latest_materialization_records_by_partition(
        AssetKey("upstream_daily_asset")
    )

    # Get all corresponding weekly partitions for any materialized daily partitions
    for partition, materialization in materializations_by_partition.items():
        weekly_partitions = context.get_downstream_partition_keys(
            partition,
            from_asset_key=AssetKey("upstream_daily_asset"),
            to_asset_key=AssetKey("downstream_weekly_asset"),
        )

        if weekly_partitions:  # Check that a downstream weekly partition exists
            # Upstream daily partition can only map to at most one downstream weekly partition
            daily_partitions_in_week = context.get_downstream_partition_keys(
                weekly_partitions[0],
                from_asset_key=AssetKey("downstream_weekly_asset"),
                to_asset_key=AssetKey("upstream_daily_asset"),
            )
            if context.all_partitions_materialized(
                AssetKey("upstream_daily_asset"), daily_partitions_in_week
            ):
                run_requests.append(
                    weekly_asset_job.run_request_for_partition(weekly_partitions[0])
                )
                # Advance the cursor so we only check event log records past the cursor
                context.advance_cursor(
                    {AssetKey("upstream_daily_asset"): materialization}
                )
    return run_requests


# end_daily_asset_to_weekly_asset

# start_multi_asset_sensor_AND


@multi_asset_sensor(
    asset_keys=[AssetKey("upstream_daily_1"), AssetKey("upstream_daily_2")],
    job=downstream_daily_job,
)
def trigger_daily_asset_if_both_upstream_partitions_materialized(context):
    run_requests = []
    for (
        partition,
        materializations_by_asset,
    ) in context.latest_materialization_records_by_partition_and_asset().items():
        if set(materializations_by_asset.keys()) == set(context.asset_keys):
            run_requests.append(
                downstream_daily_job.run_request_for_partition(partition)
            )
            for asset_key, materialization in materializations_by_asset.items():
                context.advance_cursor({asset_key: materialization})
    return run_requests


# end_multi_asset_sensor_AND


# start_multi_asset_sensor_OR
@multi_asset_sensor(
    asset_keys=[AssetKey("upstream_daily_1"), AssetKey("upstream_daily_2")],
    job=downstream_daily_job,
)
def trigger_daily_asset_when_any_upstream_partitions_replaced(context):
    run_requests = []
    for (
        partition,
        materializations_by_asset,
    ) in context.latest_materialization_records_by_partition_and_asset().items():
        if all(
            [
                context.all_partitions_materialized(asset_key, [partition])
                for asset_key in context.asset_keys
            ]
        ):
            run_requests.append(
                downstream_daily_job.run_request_for_partition(partition)
            )
            for asset_key, materialization in materializations_by_asset.items():
                if asset_key in context.asset_keys:
                    context.advance_cursor({asset_key: materialization})
    return run_requests


# end_multi_asset_sensor_OR
