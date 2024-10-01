from dagster import (
    AssetSelection,
    DailyPartitionsDefinition,
    RunRequest,
    SkipReason,
    WeeklyPartitionsDefinition,
    asset,
    define_asset_job,
    job,
    multi_asset_sensor,
)


@job
def my_job():
    pass


from typing import List

from dagster import Config


class ReadMaterializationConfig(Config):
    asset_key: List[str]


# start_asset_sensor_marker
from dagster import (
    AssetKey,
    EventLogEntry,
    RunConfig,
    SensorEvaluationContext,
    asset_sensor,
)


@asset_sensor(asset_key=AssetKey("my_table"), job=my_job)
def my_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    assert asset_event.dagster_event and asset_event.dagster_event.asset_key
    yield RunRequest(
        run_key=context.cursor,
        run_config=RunConfig(
            ops={
                "read_materialization": ReadMaterializationConfig(
                    asset_key=list(asset_event.dagster_event.asset_key.path)
                )
            }
        ),
    )


# end_asset_sensor_marker

# start_asset_sensor_test_marker
from dagster import DagsterInstance, build_sensor_context, materialize


def test_my_asset_sensor():
    @asset
    def my_table():
        return 1

    instance = DagsterInstance.ephemeral()
    ctx = build_sensor_context(instance)

    result = list(my_asset_sensor(ctx))
    assert len(result) == 1
    assert isinstance(result[0], SkipReason)

    materialize([my_table], instance=instance)

    result = list(my_asset_sensor(ctx))
    assert len(result) == 1
    assert isinstance(result[0], RunRequest)


# end_asset_sensor_test_marker


def send_alert(_msg: str) -> None:
    return


# start_freshness_policy_sensor_marker

from dagster import FreshnessPolicySensorContext, freshness_policy_sensor


@freshness_policy_sensor(asset_selection=AssetSelection.all())
def my_freshness_alerting_sensor(context: FreshnessPolicySensorContext):
    if context.minutes_overdue is None or context.previous_minutes_overdue is None:
        return

    if context.minutes_overdue >= 10 and context.previous_minutes_overdue < 10:
        send_alert(
            f"Asset with key {context.asset_key} is now more than 10 minutes overdue."
        )
    elif context.minutes_overdue == 0 and context.previous_minutes_overdue >= 10:
        send_alert(f"Asset with key {context.asset_key} is now on time.")


# end_freshness_policy_sensor_marker


# start_multi_asset_sensor_marker


@multi_asset_sensor(
    monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")],
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
    monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")],
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
def upstream_daily_1():
    return 1


@asset(partitions_def=daily_partitions_def)
def upstream_daily_2():
    return 1


@asset(partitions_def=daily_partitions_def)
def downstream_daily_asset():
    return 1


downstream_daily_job = define_asset_job(
    "downstream_daily_job",
    AssetSelection.assets(downstream_daily_asset),
    partitions_def=daily_partitions_def,
)

weekly_partitions_def = WeeklyPartitionsDefinition(start_date="2022-08-01")


@asset(partitions_def=weekly_partitions_def)
def downstream_weekly_asset():
    return 1


weekly_asset_job = define_asset_job(
    "weekly_asset_job",
    AssetSelection.assets(downstream_weekly_asset),
    partitions_def=weekly_partitions_def,
)

# start_daily_asset_to_weekly_asset


@multi_asset_sensor(
    monitored_assets=[AssetKey("upstream_daily_1")], job=weekly_asset_job
)
def trigger_weekly_asset_from_daily_asset(context):
    run_requests_by_partition = {}
    materializations_by_partition = context.latest_materialization_records_by_partition(
        AssetKey("upstream_daily_1")
    )

    # Get all corresponding weekly partitions for any materialized daily partitions
    for partition, materialization in materializations_by_partition.items():
        weekly_partitions = context.get_downstream_partition_keys(
            partition,
            from_asset_key=AssetKey("upstream_daily_1"),
            to_asset_key=AssetKey("downstream_weekly_asset"),
        )

        if weekly_partitions:  # Check that a downstream weekly partition exists
            # Upstream daily partition can only map to at most one downstream weekly partition
            daily_partitions_in_week = context.get_downstream_partition_keys(
                weekly_partitions[0],
                from_asset_key=AssetKey("downstream_weekly_asset"),
                to_asset_key=AssetKey("upstream_daily_1"),
            )
            if context.all_partitions_materialized(
                AssetKey("upstream_daily_1"), daily_partitions_in_week
            ):
                run_requests_by_partition[weekly_partitions[0]] = RunRequest(
                    partition_key=weekly_partitions[0]
                )
                # Advance the cursor so we only check event log records past the cursor
                context.advance_cursor({AssetKey("upstream_daily_1"): materialization})
    return list(run_requests_by_partition.values())


# end_daily_asset_to_weekly_asset

# start_multi_asset_sensor_AND


@multi_asset_sensor(
    monitored_assets=[
        AssetKey("upstream_daily_1"),
        AssetKey("upstream_daily_2"),
    ],
    job=downstream_daily_job,
)
def trigger_daily_asset_if_both_upstream_partitions_materialized(context):
    run_requests = []
    for (
        partition,
        materializations_by_asset,
    ) in context.latest_materialization_records_by_partition_and_asset().items():
        if set(materializations_by_asset.keys()) == set(context.asset_keys):
            run_requests.append(RunRequest(partition_key=partition))
            for asset_key, materialization in materializations_by_asset.items():
                context.advance_cursor({asset_key: materialization})
    return run_requests


# end_multi_asset_sensor_AND


# start_multi_asset_sensor_OR
@multi_asset_sensor(
    monitored_assets=[
        AssetKey("upstream_daily_1"),
        AssetKey("upstream_daily_2"),
    ],
    job=downstream_daily_job,
)
def trigger_daily_asset_when_any_upstream_partitions_have_new_materializations(context):
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
            run_requests.append(RunRequest(partition_key=partition))
            for asset_key, materialization in materializations_by_asset.items():
                if asset_key in context.asset_keys:
                    context.advance_cursor({asset_key: materialization})
    return run_requests


# end_multi_asset_sensor_OR
