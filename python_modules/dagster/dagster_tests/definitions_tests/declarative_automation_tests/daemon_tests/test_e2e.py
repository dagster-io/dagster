import datetime
import os
import sys
from contextlib import contextmanager
from typing import AbstractSet, Mapping, Sequence, cast

import dagster._check as check
from dagster import AssetMaterialization, RunsFilter, instance_for_test
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.remote_representation.external import ExternalSensor
from dagster._core.remote_representation.origin import InProcessCodeLocationOrigin
from dagster._core.scheduler.instigation import InstigatorState, SensorInstigatorData
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    freeze_time,
    wait_for_futures,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._daemon.asset_daemon import (
    AssetDaemon,
    asset_daemon_cursor_from_instigator_serialized_cursor,
)
from dagster._daemon.daemon import get_default_daemon_logger
from dagster._daemon.sensor import execute_sensor_iteration
from dagster._time import get_current_datetime


def get_code_location_origin(filename: str) -> InProcessCodeLocationOrigin:
    return InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.definitions_tests.declarative_automation_tests.daemon_tests.definitions.{filename}"
            ),
            working_directory=os.getcwd(),
        ),
        location_name=filename,
    )


def _get_all_sensors(context: WorkspaceRequestContext) -> Sequence[ExternalSensor]:
    external_sensors = []
    for cl_name in context.get_code_location_entries():
        external_sensors.extend(
            next(
                iter(context.get_code_location(cl_name).get_repositories().values())
            ).get_external_sensors()
        )
    return external_sensors


def _get_automation_sensors(context: WorkspaceRequestContext) -> Sequence[ExternalSensor]:
    return [
        sensor
        for sensor in _get_all_sensors(context)
        if sensor.sensor_type in (SensorType.AUTO_MATERIALIZE, SensorType.AUTOMATION)
    ]


def _setup_instance(context: WorkspaceProcessContext) -> None:
    """Does any initialization necessary."""
    request_context = context.create_request_context()
    sensors = _get_automation_sensors(request_context)
    for sensor in sensors:
        request_context.instance.start_sensor(sensor)


@contextmanager
def get_workspace_request_context(filenames: Sequence[str]):
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
        }
    ) as instance:
        target = InProcessTestWorkspaceLoadTarget(
            [get_code_location_origin(filename) for filename in filenames]
        )
        with create_test_daemon_workspace_context(
            workspace_load_target=target, instance=instance
        ) as workspace_context:
            _setup_instance(workspace_context)
            yield workspace_context


@contextmanager
def get_threadpool_executor():
    with SingleThreadPoolExecutor() as executor:
        yield executor


def _execute_ticks(
    context: WorkspaceProcessContext, threadpool_executor: InheritContextThreadPoolExecutor
) -> None:
    """Evaluates a single tick for all automation condition sensors across the workspace.
    Evaluates an iteration of both the AssetDaemon and the SensorDaemon as either can handle
    an AutomationConditionSensorDefinition depending on the user_code setting.
    """
    asset_daemon_futures = {}
    list(
        AssetDaemon(settings={}, pre_sensor_interval_seconds=0)._run_iteration_impl(  # noqa
            context,
            threadpool_executor=threadpool_executor,
            amp_tick_futures=asset_daemon_futures,
            debug_crash_flags={},
        )
    )

    sensor_daemon_futures = {}
    list(
        execute_sensor_iteration(
            context,
            get_default_daemon_logger("SensorDaemon"),
            threadpool_executor=threadpool_executor,
            sensor_tick_futures=sensor_daemon_futures,
            submit_threadpool_executor=None,
        )
    )

    wait_for_futures(asset_daemon_futures)
    wait_for_futures(sensor_daemon_futures)


def _get_current_state(context: WorkspaceRequestContext) -> Mapping[str, InstigatorState]:
    state_by_name = {}
    for sensor in _get_automation_sensors(context):
        state = check.not_none(
            context.instance.get_instigator_state(
                sensor.get_external_origin_id(), sensor.selector_id
            )
        )
        state_by_name[f"{sensor.name}_{sensor.get_external_origin_id()}"] = state
    return state_by_name


def _get_current_cursors(context: WorkspaceProcessContext) -> Mapping[str, AssetDaemonCursor]:
    request_context = context.create_request_context()

    return {
        name: asset_daemon_cursor_from_instigator_serialized_cursor(
            cast(SensorInstigatorData, check.not_none(state).instigator_data).cursor,
            request_context.asset_graph,
        )
        for name, state in _get_current_state(request_context).items()
    }


def _get_latest_evaluation_ids(context: WorkspaceProcessContext) -> AbstractSet[int]:
    return {cursor.evaluation_id for cursor in _get_current_cursors(context).values()}


def _get_runs_for_latest_ticks(context: WorkspaceProcessContext) -> Sequence[DagsterRun]:
    run_ids = []
    request_context = context.create_request_context()
    for sensor in _get_automation_sensors(request_context):
        ticks = request_context.instance.get_ticks(
            sensor.get_external_origin_id(),
            sensor.get_external_origin().get_selector().get_id(),
            limit=1,
        )
        latest_tick = next(iter(ticks), None)
        if latest_tick and latest_tick.tick_data:
            run_ids.extend(latest_tick.tick_data.reserved_run_ids or [])

    if run_ids:
        return context.instance.get_runs(filters=RunsFilter(run_ids=run_ids))
    else:
        return []


def test_checks_and_assets_in_same_run() -> None:
    time = get_current_datetime()
    with get_workspace_request_context(
        ["check_after_parent_updated"]
    ) as context, get_threadpool_executor() as executor:
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)

            # nothing happening yet, as parent hasn't updated
            assert _get_latest_evaluation_ids(context) == {1}
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset in the middle
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)

            # should just request the check
            assert _get_latest_evaluation_ids(context) == {2}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }
            assert len(run.asset_selection or []) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset at the top
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("raw_files"))
            )

            _execute_ticks(context, executor)

            # should create a single run request targeting both the downstream asset
            # and the associated check
            assert _get_latest_evaluation_ids(context) == {3}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {AssetKey("processed_files")}
            assert run.asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }


def test_cross_location_checks() -> None:
    time = get_current_datetime()
    with get_workspace_request_context(
        ["check_on_other_location", "check_after_parent_updated"]
    ) as context, get_threadpool_executor() as executor:
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)

            # nothing happening yet, as parent hasn't updated
            assert _get_latest_evaluation_ids(context) == {1, 2}
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset in the middle
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)

            # should request both checks on processed_files, but one of the checks
            # is in a different code location, so two separate runs should be created
            assert _get_latest_evaluation_ids(context) == {3, 4}
            runs = sorted(
                _get_runs_for_latest_ticks(context),
                key=lambda run: list(run.asset_check_selection or []),
                reverse=True,
            )
            assert len(runs) == 2
            # in location 1
            assert runs[0].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }
            assert len(runs[0].asset_selection or []) == 0
            # in location 2
            assert runs[1].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "no_nulls")
            }
            assert len(runs[1].asset_selection or []) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset at the top
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("raw_files"))
            )

            _execute_ticks(context, executor)

            # should create a single run request targeting both the downstream asset
            # and the associated check -- the check in the other location cannot
            # be grouped with these and will need to wait
            assert _get_latest_evaluation_ids(context) == {5, 6}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {AssetKey("processed_files")}
            assert run.asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            _execute_ticks(context, executor)

            # now, after processed_files gets materialized, the no_nulls check
            # can be executed (and row_count also gets executed again because
            # its condition has been set up poorly)
            assert _get_latest_evaluation_ids(context) == {7, 8}
            runs = sorted(
                _get_runs_for_latest_ticks(context),
                key=lambda run: list(run.asset_check_selection or []),
                reverse=True,
            )
            assert len(runs) == 2
            # in location 1
            assert runs[0].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }
            assert len(runs[0].asset_selection or []) == 0
            # in location 2
            assert runs[1].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "no_nulls")
            }
            assert len(runs[1].asset_selection or []) == 0


def test_default_condition() -> None:
    time = datetime.datetime(2024, 8, 16, 4)
    with get_workspace_request_context(
        ["default_condition"]
    ) as context, get_threadpool_executor() as executor:
        with freeze_time(time):
            _execute_ticks(context, executor)

            # eager asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {AssetKey("eager_asset")}

        time += datetime.timedelta(seconds=60)
        with freeze_time(time):
            _execute_ticks(context, executor)

            # passed a cron tick, so cron asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {AssetKey("every_5_minutes_asset")}
