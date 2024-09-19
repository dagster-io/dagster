import os

from dagster import (
    AssetCheckKey,
    AssetSelection,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    RunRequest,
    asset,
    asset_check,
    sensor,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.test_utils import create_test_daemon_workspace_context, load_external_repo
from dagster._core.workspace.load_target import ModuleTarget

from dagster_tests.daemon_sensor_tests.test_sensor_run import evaluate_sensors, validate_tick


@asset(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))
def asset_one(): ...


@asset(partitions_def=DailyPartitionsDefinition(start_date="2024-02-01"))
def asset_two(): ...


@asset_check(asset=asset_two)
def check1():
    raise NotImplementedError()


@sensor(asset_selection=AssetSelection.checks(check1))
def asset_check_run_request_sensor():
    return RunRequest(asset_check_keys=[AssetCheckKey(asset_two.key, "check1")])


defs = Definitions(
    assets=[asset_one, asset_two],
    asset_checks=[check1],
    sensors=[asset_check_run_request_sensor],
)


module_target = ModuleTarget(
    module_name="dagster_tests.daemon_sensor_tests.test_sensor_run_asset_checks",
    attribute=None,
    working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
    location_name="test_location",
)


def test_asset_check_run_request_sensor(instance: DagsterInstance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(asset_check_run_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1

        run = instance.get_runs()[0]
        validate_tick(
            ticks[0],
            external_sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[run.run_id],
        )
