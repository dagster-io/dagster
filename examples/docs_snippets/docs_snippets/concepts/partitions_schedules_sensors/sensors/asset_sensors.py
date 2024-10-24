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
