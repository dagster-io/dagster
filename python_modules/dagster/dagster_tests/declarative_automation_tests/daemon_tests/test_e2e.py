import datetime
import os
import sys
import time
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from typing import AbstractSet, Any, Optional, cast  # noqa: UP035

import dagster._check as check
import pytest
from dagster import AssetMaterialization, RunsFilter, instance_for_test
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.remote_representation.external import RemoteSensor
from dagster._core.remote_representation.origin import InProcessCodeLocationOrigin
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorTick,
    SensorInstigatorData,
    TickStatus,
)
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
from dagster._core.workspace.load_target import GrpcServerTarget
from dagster._daemon.asset_daemon import (
    AssetDaemon,
    asset_daemon_cursor_from_instigator_serialized_cursor,
)
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._daemon.daemon import get_default_daemon_logger
from dagster._daemon.sensor import execute_sensor_iteration
from dagster._grpc.server import GrpcServerProcess
from dagster._time import get_current_datetime


def get_loadable_target_origin(filename: str) -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name=(
            f"dagster_tests.declarative_automation_tests.daemon_tests.definitions.{filename}"
        ),
        working_directory=os.getcwd(),
    )


def get_code_location_origin(
    filename: str, location_name: Optional[str] = None
) -> InProcessCodeLocationOrigin:
    return InProcessCodeLocationOrigin(
        loadable_target_origin=get_loadable_target_origin(filename),
        location_name=location_name or filename,
    )


def _get_all_sensors(context: WorkspaceRequestContext) -> Sequence[RemoteSensor]:
    sensors = []
    for cl_name in context.get_code_location_entries():
        sensors.extend(
            next(iter(context.get_code_location(cl_name).get_repositories().values())).get_sensors()
        )
    return sensors


def _get_automation_sensors(context: WorkspaceRequestContext) -> Sequence[RemoteSensor]:
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
def get_workspace_request_context(
    filenames: Sequence[str], overrides: Optional[dict[str, Any]] = None
):
    with instance_for_test(
        overrides=overrides,
        synchronous_run_launcher=True,
        synchronous_run_coordinator=True,
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
def get_grpc_workspace_request_context(filename: str, instance_ref: Optional[InstanceRef] = None):
    with (
        DagsterInstance.from_ref(instance_ref) if instance_ref else instance_for_test()
    ) as instance:
        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=get_loadable_target_origin(filename),
            max_workers=4,
            wait_on_exit=True,
        ) as server_process:
            target = GrpcServerTarget(
                host="localhost",
                socket=server_process.socket,
                port=server_process.port,
                location_name="test",
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
    context: WorkspaceProcessContext,
    threadpool_executor: InheritContextThreadPoolExecutor,
    submit_threadpool_executor: Optional[InheritContextThreadPoolExecutor] = None,
    debug_crash_flags=None,
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
            debug_crash_flags=debug_crash_flags or {},
            submit_threadpool_executor=submit_threadpool_executor,
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

    backfill_daemon_futures = {}
    list(
        execute_backfill_iteration(
            context,
            get_default_daemon_logger("BackfillDaemon"),
            threadpool_executor=threadpool_executor,
            backfill_futures=backfill_daemon_futures,
            debug_crash_flags=debug_crash_flags or {},
        )
    )

    wait_for_futures(asset_daemon_futures)
    wait_for_futures(sensor_daemon_futures)
    wait_for_futures(backfill_daemon_futures)


def _get_current_state(context: WorkspaceRequestContext) -> Mapping[str, InstigatorState]:
    state_by_name = {}
    for sensor in _get_automation_sensors(context):
        state = check.not_none(
            context.instance.get_instigator_state(sensor.get_remote_origin_id(), sensor.selector_id)
        )
        state_by_name[f"{sensor.name}_{sensor.get_remote_origin_id()}"] = state
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


def _get_latest_ticks(context: WorkspaceRequestContext) -> Sequence[InstigatorTick]:
    latest_ticks = []
    for sensor in _get_automation_sensors(context):
        ticks = context.instance.get_ticks(
            sensor.get_remote_origin_id(),
            sensor.get_remote_origin().get_selector().get_id(),
            limit=1,
        )
        latest_ticks.extend(ticks)
    return latest_ticks


def _get_reserved_ids_for_latest_ticks(context: WorkspaceProcessContext) -> Sequence[str]:
    ids = []
    request_context = context.create_request_context()
    for latest_tick in _get_latest_ticks(request_context):
        if latest_tick.tick_data:
            ids.extend(latest_tick.tick_data.reserved_run_ids or [])
    return ids


def _get_runs_for_latest_ticks(context: WorkspaceProcessContext) -> Sequence[DagsterRun]:
    reserved_ids = _get_reserved_ids_for_latest_ticks(context)
    if reserved_ids:
        # return the runs in a stable order to make unit testing easier
        return sorted(
            context.instance.get_runs(filters=RunsFilter(run_ids=reserved_ids)),
            key=lambda r: (sorted(r.asset_selection or []), sorted(r.asset_check_selection or [])),
        )
    else:
        return []


def _get_backfills_for_latest_ticks(
    context: WorkspaceProcessContext,
) -> Sequence[PartitionBackfill]:
    reserved_ids = _get_reserved_ids_for_latest_ticks(context)
    backfills = []
    for rid in reserved_ids:
        backfill = context.instance.get_backfill(rid)
        if backfill:
            backfills.append(backfill)
    return sorted(backfills, key=lambda b: sorted(b.asset_selection))


def test_checks_and_assets_in_same_run() -> None:
    time = get_current_datetime()
    with (
        get_workspace_request_context(["check_after_parent_updated"]) as context,
        get_threadpool_executor() as executor,
    ):
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # nothing happening yet, as parent hasn't updated
            assert _get_latest_evaluation_ids(context) == {1}
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset in the middle
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

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

            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

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
    with (
        get_workspace_request_context(
            ["check_on_other_location", "check_after_parent_updated"]
        ) as context,
        get_threadpool_executor() as executor,
    ):
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # nothing happening yet, as parent hasn't updated
            assert _get_latest_evaluation_ids(context) == {1, 2}
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset in the middle
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # should request both checks on processed_files, but one of the checks
            # is in a different code location, so two separate runs should be created
            assert _get_latest_evaluation_ids(context) == {3, 4}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2
            # in location 1
            assert runs[1].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }
            assert len(runs[1].asset_selection or []) == 0
            # in location 2
            assert runs[0].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "no_nulls")
            }
            assert len(runs[0].asset_selection or []) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset at the top
            context.instance.report_runless_asset_event(
                AssetMaterialization(asset_key=AssetKey("raw_files"))
            )

            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

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
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # now, after processed_files gets materialized, the no_nulls check
            # can be executed (and row_count also gets executed again because
            # its condition has been set up poorly)
            assert _get_latest_evaluation_ids(context) == {7, 8}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2
            # in location 1
            assert runs[1].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "row_count")
            }
            assert len(runs[1].asset_selection or []) == 0
            # in location 2
            assert runs[0].asset_check_selection == {
                AssetCheckKey(AssetKey("processed_files"), "no_nulls")
            }
            assert len(runs[0].asset_selection or []) == 0


def test_default_condition() -> None:
    time = datetime.datetime(2024, 8, 16, 4)
    with (
        get_workspace_request_context(["default_condition"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # eager asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {AssetKey("eager_asset")}

        time += datetime.timedelta(seconds=60)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            # passed a cron tick, so cron asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {AssetKey("every_5_minutes_asset")}


def test_non_subsettable_check() -> None:
    with (
        get_grpc_workspace_request_context("check_not_subsettable") as context,
        get_threadpool_executor() as executor,
        InheritContextThreadPoolExecutor(max_workers=5) as submit_executor,
    ):
        time = datetime.datetime(2024, 8, 17, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor, submit_executor)  # pyright: ignore[reportArgumentType]

            # eager asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 3

            # unpartitioned
            unpartitioned_run = runs[2]
            assert unpartitioned_run.tags.get("dagster/partition") is None
            assert unpartitioned_run.asset_selection == {AssetKey("unpartitioned")}
            assert unpartitioned_run.asset_check_selection == {
                AssetCheckKey(AssetKey("unpartitioned"), name="row_count")
            }

            # static partitioned
            static_partitioned_run = runs[1]
            assert static_partitioned_run.tags.get("dagster/partition") == "a"
            assert static_partitioned_run.asset_selection == {AssetKey("static")}
            assert static_partitioned_run.asset_check_selection == {
                AssetCheckKey(AssetKey("static"), name="c1"),
                AssetCheckKey(AssetKey("static"), name="c2"),
            }

            # multi-asset time partitioned
            time_partitioned_run = runs[0]
            assert time_partitioned_run.tags.get("dagster/partition") == "2024-08-16"
            assert time_partitioned_run.asset_selection == {
                AssetKey("a"),
                AssetKey("b"),
                AssetKey("c"),
                AssetKey("d"),
            }
            assert time_partitioned_run.asset_check_selection == {
                AssetCheckKey(AssetKey("a"), name="1"),
                AssetCheckKey(AssetKey("a"), name="2"),
                AssetCheckKey(AssetKey("d"), name="3"),
            }


def _get_subsets_by_key(
    backfill: PartitionBackfill, asset_graph: BaseAssetGraph
) -> Mapping[AssetKey, SerializableEntitySubset[AssetKey]]:
    assert backfill.asset_backfill_data is not None
    target_subset = backfill.asset_backfill_data.target_subset
    return {s.key: s for s in target_subset.iterate_asset_subsets(asset_graph)}


@pytest.mark.parametrize("location", ["backfill_simple_user_code", "backfill_simple_non_user_code"])
def test_backfill_creation_simple(location: str) -> None:
    with (
        get_workspace_request_context([location]) as context,
        get_threadpool_executor() as executor,
    ):
        asset_graph = context.create_request_context().asset_graph

        # all start off missing, should be requested
        time = get_current_datetime()
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {
                AssetKey("A"),
                AssetKey("B"),
                AssetKey("C"),
                AssetKey("D"),
                AssetKey("E"),
            }

            assert subsets_by_key[AssetKey("A")].size == 1
            assert subsets_by_key[AssetKey("B")].size == 3
            assert subsets_by_key[AssetKey("C")].size == 3
            assert subsets_by_key[AssetKey("D")].size == 3
            assert subsets_by_key[AssetKey("E")].size == 1

            # don't create runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # second tick, don't kick off again
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0
            # still don't create runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_backfill_with_runs_and_checks() -> None:
    with (
        get_grpc_workspace_request_context("backfill_with_runs_and_checks") as context,
        get_threadpool_executor() as executor,
    ):
        asset_graph = context.create_request_context().asset_graph

        # report materializations for 2/3 of the partitions, resulting in only one
        # partition needing to be requested
        context.instance.report_runless_asset_event(AssetMaterialization("run2", partition="x"))
        context.instance.report_runless_asset_event(AssetMaterialization("run2", partition="y"))

        # all start off missing, should be requested
        time = get_current_datetime()
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            # create a backfill for the part of the graph that has multiple partitions
            # required
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {
                AssetKey("backfillA"),
                AssetKey("backfillB"),
                AssetKey("backfillC"),
            }

            assert subsets_by_key[AssetKey("backfillA")].size == 1
            assert subsets_by_key[AssetKey("backfillB")].size == 3
            assert subsets_by_key[AssetKey("backfillC")].size == 3

            # create 2 individual runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2

            # unpartitioned
            unpartitioned_run = runs[0]
            assert unpartitioned_run.tags.get("dagster/partition") is None
            assert unpartitioned_run.asset_selection == {AssetKey("run1")}
            assert unpartitioned_run.asset_check_selection == {
                AssetCheckKey(AssetKey("run1"), name="inside")
            }

            # static partitioned 1
            static_partitioned_run = runs[1]
            assert static_partitioned_run.tags.get("dagster/partition") == "z"
            assert static_partitioned_run.asset_selection == {AssetKey("run2")}
            assert static_partitioned_run.asset_check_selection == {
                AssetCheckKey(AssetKey("run2"), name="inside")
            }

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # second tick, don't kick off again
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]

            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_toggle_user_code() -> None:
    with (
        instance_for_test(
            synchronous_run_launcher=True,
            synchronous_run_coordinator=True,
        ) as instance,
        get_threadpool_executor() as executor,
    ):
        user_code_target = InProcessTestWorkspaceLoadTarget(
            [get_code_location_origin("simple_user_code", location_name="simple")]
        )
        non_user_code_target = InProcessTestWorkspaceLoadTarget(
            [get_code_location_origin("simple_non_user_code", location_name="simple")]
        )

        # start off with non user code target, just do the setup once
        with create_test_daemon_workspace_context(
            workspace_load_target=non_user_code_target, instance=instance
        ) as context:
            _setup_instance(context)

        time = get_current_datetime()
        # toggle back and forth between target types
        for target in [non_user_code_target, user_code_target, non_user_code_target]:
            with create_test_daemon_workspace_context(
                workspace_load_target=target, instance=instance
            ) as context:
                time += datetime.timedelta(seconds=35)
                with freeze_time(time):
                    # first tick, nothing happened
                    _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
                    runs = _get_runs_for_latest_ticks(context)
                    assert len(runs) == 0

                time += datetime.timedelta(seconds=35)
                with freeze_time(time):
                    # second tick, root gets updated
                    instance.report_runless_asset_event(AssetMaterialization("root"))
                    _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
                    runs = _get_runs_for_latest_ticks(context)
                    assert runs[0].asset_selection == {AssetKey("downstream")}

                time += datetime.timedelta(seconds=35)
                with freeze_time(time):
                    # third tick, don't kick off again
                    _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
                    runs = _get_runs_for_latest_ticks(context)
                    assert len(runs) == 0


def test_custom_condition() -> None:
    with (
        get_grpc_workspace_request_context("custom_condition") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)

        # custom condition only materializes on the 5th tick
        for _ in range(4):
            with freeze_time(time):
                _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
                runs = _get_runs_for_latest_ticks(context)
                assert len(runs) == 0
            time += datetime.timedelta(minutes=1)

        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1

        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_500_eager_assets_user_code(capsys) -> None:
    with (
        get_grpc_workspace_request_context("500_eager_assets") as context,
        get_threadpool_executor() as executor,
    ):
        freeze_dt = datetime.datetime(2024, 8, 16, 1, 35)

        for _ in range(2):
            clock_time = time.time()
            with freeze_time(freeze_dt):
                _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
                runs = _get_runs_for_latest_ticks(context)
                assert len(runs) == 0
            duration = time.time() - clock_time
            assert duration < 40.0

            freeze_dt += datetime.timedelta(minutes=1)

            latest_ticks = _get_latest_ticks(context.create_request_context())
            assert len(latest_ticks) == 1
            # no failure
            assert latest_ticks[0].status == TickStatus.SKIPPED

    # more specific check
    assert "RESOURCE_EXHAUSTED" not in capsys.readouterr().out


def test_fail_if_not_use_sensors(capsys) -> None:
    with (
        get_workspace_request_context(
            ["simple_user_code"], overrides={"auto_materialize": {"use_sensors": False}}
        ) as context,
        get_threadpool_executor() as executor,
    ):
        _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
        latest_ticks = _get_latest_ticks(context.create_request_context())
        assert len(latest_ticks) == 1
        # no failure
        assert latest_ticks[0].status == TickStatus.FAILURE
        assert (
            "Cannot evaluate an AutomationConditionSensorDefinition if the instance setting `auto_materialize: use_sensors` is set to False"
            in capsys.readouterr().out
        )


def test_simple_old_code_server() -> None:
    with (
        get_grpc_workspace_request_context("old_code_server_simulation") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            # initial evaluation
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1


def test_observable_source_asset() -> None:
    with (
        get_grpc_workspace_request_context("hourly_observable") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        time += datetime.timedelta(hours=1)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {AssetKey("obs"), AssetKey("mat")}

        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_observable_source_asset_is_not_backfilled() -> None:
    with (
        get_grpc_workspace_request_context("hourly_observable_with_partitions") as context,
        get_threadpool_executor() as executor,
    ):
        asset_graph = context.create_request_context().asset_graph

        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0

        time += datetime.timedelta(hours=1)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 3
            assert all(run.asset_selection == {AssetKey("obs")} for run in runs)
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {AssetKey("mat")}

        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)  # pyright: ignore[reportArgumentType]
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0
