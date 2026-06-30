import datetime
import multiprocessing.process
import os
import sys
import time
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from typing import AbstractSet, Any, cast  # noqa: UP035
from unittest import mock

import dagster as dg
import dagster._check as check
import pytest
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.instance import DagsterInstance
from dagster._core.instance.methods.asset_methods import AssetMethods
from dagster._core.instance.ref import InstanceRef
from dagster._core.remote_origin import InProcessCodeLocationOrigin
from dagster._core.remote_representation.external import RemoteSensor
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
    filename: str, location_name: str | None = None
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
    filenames: Sequence[str | tuple[str, str]], overrides: dict[str, Any] | None = None
):
    with dg.instance_for_test(
        overrides=overrides,
        synchronous_run_launcher=True,
        synchronous_run_coordinator=True,
    ) as instance:
        target = InProcessTestWorkspaceLoadTarget(
            [
                get_code_location_origin(
                    filename[0] if isinstance(filename, tuple) else filename,
                    filename[1] if isinstance(filename, tuple) else None,
                )
                for filename in filenames
            ]
        )
        with create_test_daemon_workspace_context(
            workspace_load_target=target, instance=instance
        ) as workspace_context:
            _setup_instance(workspace_context)
            yield workspace_context


@contextmanager
def get_grpc_workspace_request_context(filename: str, instance_ref: InstanceRef | None = None):
    with (
        DagsterInstance.from_ref(instance_ref) if instance_ref else dg.instance_for_test()
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


def wait_for_daemon_subprocess(
    process: multiprocessing.process.BaseProcess,
    *,
    timeout: float = 180.0,
    poll_interval: float = 0.5,
) -> None:
    deadline = time.monotonic() + timeout
    while process.is_alive() and time.monotonic() < deadline:
        process.join(timeout=poll_interval)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        raise RuntimeError(f"Daemon subprocess (pid={process.pid}) did not exit within {timeout}s")


def _execute_ticks(
    context: WorkspaceProcessContext,
    threadpool_executor: InheritContextThreadPoolExecutor,
    debug_crash_flags=None,
) -> None:
    """Evaluates a single tick for all automation condition sensors across the workspace.
    Evaluates an iteration of both the AssetDaemon and the SensorDaemon as either can handle
    an AutomationConditionSensorDefinition depending on the user_code setting.
    """
    asset_daemon_futures = {}
    AssetDaemon(settings={}, pre_sensor_interval_seconds=0)._run_iteration_impl(  # noqa
        context,
        threadpool_executor=threadpool_executor,
        amp_tick_futures=asset_daemon_futures,
        debug_crash_flags=debug_crash_flags or {},
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
            cast("SensorInstigatorData", check.not_none(state).instigator_data).cursor,
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


def _get_runs_for_latest_ticks(context: WorkspaceProcessContext) -> Sequence[dg.DagsterRun]:
    reserved_ids = _get_reserved_ids_for_latest_ticks(context)
    if reserved_ids:
        # return the runs in a stable order to make unit testing easier
        return sorted(
            context.instance.get_runs(filters=dg.RunsFilter(run_ids=reserved_ids)),
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
    return sorted(backfills, key=lambda b: sorted(b.asset_selection or []))


def test_checks_and_assets_in_same_run() -> None:
    time = get_current_datetime()
    with (
        get_workspace_request_context(["check_after_parent_updated"]) as context,
        get_threadpool_executor() as executor,
    ):
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
                dg.AssetMaterialization(asset_key=dg.AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)

            # should just request the check
            assert _get_latest_evaluation_ids(context) == {2}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")
            }
            assert len(run.asset_selection or []) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset at the top
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )

            _execute_ticks(context, executor)

            # should create a single run request targeting both the downstream asset
            # and the associated check
            assert _get_latest_evaluation_ids(context) == {3}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            assert run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")
            }


@contextmanager
def _resolve_check_keys_gate(enabled: bool):
    """Toggle the declarative-automation asset-check-resolution feature gate for a test by patching
    the instance method that Dagster Cloud overrides to consult Statsig.
    """
    with mock.patch.object(
        AssetMethods, "automation_resolve_asset_check_keys_enabled", return_value=enabled
    ):
        yield


@pytest.mark.parametrize("gate_enabled", [True, False])
def test_no_da_checks_falls_back_to_none_selection(gate_enabled: bool) -> None:
    # `processed_files` is requested by an automation tick, and neither of its checks
    # (`row_count`, `non_null`) uses declarative automation. Whether or not the feature is enabled,
    # the run records `asset_check_selection=None`
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(["check_without_condition"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            # nothing yet -- parent hasn't updated
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # update the parent so `processed_files` eager condition fires
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            assert run.asset_check_selection is None


@pytest.mark.parametrize(
    "gate_enabled, expected_check_selection",
    [
        # gate on: explicitly-requested `row_count` unioned with the unconditioned ride-along
        # `non_null`.
        (
            True,
            {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count"),
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "non_null"),
            },
        ),
        # gate off: legacy behavior -- only the explicitly-requested check, no ride-along union.
        (False, {dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")}),
    ],
)
def test_requested_conditioned_check_selection(gate_enabled, expected_check_selection) -> None:
    # `processed_files` has a conditional `row_count` check and an unconditional `non_null` check.
    # Updating `raw_files` requests `processed_files` AND fires `row_count`'s condition, but does
    # not fire any condition for `non_null` (it has none).
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(["check_subset_with_unconditioned_sibling"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            # nothing yet -- parent hasn't updated
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            assert run.asset_check_selection == expected_check_selection


@pytest.mark.parametrize(
    "gate_enabled, expected_check_selection",
    [
        # gate on: only the unconditioned `non_null` rides along; `yearly_check` is excluded from
        # the default set because it owns an automation condition (and did not fire this tick).
        (True, {dg.AssetCheckKey(dg.AssetKey("processed_files"), "non_null")}),
        # gate off: legacy behavior -- no check was explicitly requested, so None is recorded.
        (False, None),
    ],
)
def test_unconditioned_default_check_selection(gate_enabled, expected_check_selection) -> None:
    # `processed_files` has `yearly_check` (owns an automation condition that does NOT fire in the
    # test window) and `non_null` (no condition). Updating `raw_files` requests `processed_files`
    # with no check individually requested.
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(["check_conditioned_sibling_not_firing"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            assert run.asset_check_selection == expected_check_selection


@pytest.mark.parametrize(
    "gate_enabled, expected_check_selection",
    [
        # gate on: requested `row_count` unioned with the unconditioned sibling `non_null`.
        (
            True,
            {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count"),
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "non_null"),
            },
        ),
        # gate off: legacy -- only the explicitly-requested `row_count`.
        (False, {dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")}),
    ],
)
def test_check_on_other_asset_not_included(gate_enabled, expected_check_selection) -> None:
    # `processed_files` is requested with a conditioned `row_count` check (which fires) and an
    # unconditioned `non_null` sibling. `other_check` targets a DIFFERENT asset (`other_asset`), so
    # it must NOT be attached to `processed_files`'s run -- in either gate state.
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(["check_on_other_asset_excluded"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            assert run.asset_check_selection == expected_check_selection
            # `other_check` (on `other_asset`) is never attached -- it targets a different asset
            assert dg.AssetCheckKey(dg.AssetKey("other_asset"), "other_check") not in (
                run.asset_check_selection or set()
            )


@pytest.mark.parametrize("gate_enabled", [True, False])
def test_cross_location_check_excluded_from_ride_along(gate_enabled: bool) -> None:
    # `processed_files` (location A) has a SAME-location conditioned check `row_count` (which fires)
    # plus an unconditioned check `external_not_null` in a DIFFERENT location. The run records only
    # `row_count`; `external_not_null` is excluded in either gate state (gate on: by the ride-along
    # repo-filter; gate off: it was never requested). With the gate ON this specifically exercises
    # the repo-filter branch of `_ride_along_check_keys_for_assets`, which the no-DA-check
    # cross-location case (fast-path) does not reach -- and building the run must not fail.
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(
            ["cross_location_da_check_asset", "cross_location_da_check_other"]
        ) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            run = next(r for r in runs if r.asset_selection == {dg.AssetKey("processed_files")})
            # only the same-location check; the other-location `external_not_null` is repo-filtered
            assert run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")
            }
            assert dg.AssetCheckKey(dg.AssetKey("processed_files"), "external_not_null") not in (
                run.asset_check_selection or set()
            )


def _get_location_name(run: DagsterRun):
    return check.not_none(
        run.remote_job_origin
    ).repository_origin.code_location_origin.location_name


def test_cross_location_source_assets() -> None:
    time = get_current_datetime()
    with (
        get_workspace_request_context(["defs_with_source_assets", "always_evaluates"]) as context,
        get_threadpool_executor() as executor,
    ):
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)
            # observable source asset executes
            assert _get_latest_evaluation_ids(context) == {1, 2}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2
            assert any(
                run.asset_selection == {dg.AssetKey("foo_source_asset")}
                and _get_location_name(run) == "defs_with_source_assets"
                for run in runs
            )
            assert any(
                run.asset_selection == {dg.AssetKey("always")}
                and _get_location_name(run) == "always_evaluates"
                for run in runs
            )


def test_multiple_materializable_breaks_ties() -> None:
    time = get_current_datetime()
    with (
        get_workspace_request_context(
            [("always_evaluates", "always_1"), ("always_evaluates", "always_2")]
        ) as context,
        get_threadpool_executor() as executor,
    ):
        assert _get_latest_evaluation_ids(context) == {0}
        assert _get_runs_for_latest_ticks(context) == []

        with freeze_time(time):
            _execute_ticks(context, executor)
            # observable source asset executes
            assert _get_latest_evaluation_ids(context) == {
                0,
                1,
            }  # only one sensor has assets to evaluate
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {dg.AssetKey("always")}


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
            _execute_ticks(context, executor)

            # nothing happening yet, as parent hasn't updated
            assert _get_latest_evaluation_ids(context) == {1, 2}
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset in the middle
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("processed_files"))
            )

            _execute_ticks(context, executor)

            # should request both checks on processed_files, but one of the checks
            # is in a different code location, so two separate runs should be created
            assert _get_latest_evaluation_ids(context) == {3, 4}
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2
            # in location 1
            assert runs[1].asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")
            }
            assert len(runs[1].asset_selection or []) == 0
            # in location 2
            assert runs[0].asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("processed_files"), "no_nulls")
            }
            assert len(runs[0].asset_selection or []) == 0

        row_count_key = dg.AssetCheckKey(dg.AssetKey("processed_files"), "row_count")
        no_nulls_key = dg.AssetCheckKey(dg.AssetKey("processed_files"), "no_nulls")

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # now update the asset at the top
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )

            _execute_ticks(context, executor)

            # A combined run is always produced for processed_files + row_count
            # (raw_files newly updated -> eager processed_files will-be-requested
            # -> same-location row_count fires alongside in the same run). The
            # no_nulls check lives in a different code location and cannot be
            # grouped into that run.
            #
            # Whether no_nulls also fires in this same tick is non-deterministic:
            # the asset daemon round-robins across code locations, and the test
            # uses a synchronous run launcher, so if the row_count sensor is
            # visited first its run completes (materializing processed_files)
            # before no_nulls evaluates -- letting no_nulls see the new
            # materialization and fire immediately. Otherwise no_nulls waits
            # for the next tick.
            assert _get_latest_evaluation_ids(context) == {5, 6}
            runs = _get_runs_for_latest_ticks(context)
            combined_run = next(
                r for r in runs if r.asset_selection == {dg.AssetKey("processed_files")}
            )
            assert combined_run.asset_check_selection == {row_count_key}
            no_nulls_fired_early = any(r.asset_check_selection == {no_nulls_key} for r in runs)
            assert len(runs) == (2 if no_nulls_fired_early else 1)

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            _execute_ticks(context, executor)

            # row_count is always re-requested here because its condition is set
            # up loosely (any-dep newly_updated re-fires on the just-completed
            # processed_files materialization). no_nulls is only re-requested if
            # it didn't already fire in the previous tick.
            assert _get_latest_evaluation_ids(context) == {7, 8}
            runs = _get_runs_for_latest_ticks(context)
            row_count_run = next(r for r in runs if r.asset_check_selection == {row_count_key})
            assert len(row_count_run.asset_selection or []) == 0
            if no_nulls_fired_early:
                assert len(runs) == 1
            else:
                assert len(runs) == 2
                no_nulls_run = next(r for r in runs if r.asset_check_selection == {no_nulls_key})
                assert len(no_nulls_run.asset_selection or []) == 0


@pytest.mark.parametrize("gate_enabled", [True, False])
def test_unconditioned_check_in_other_location_not_pulled_into_asset_run(
    gate_enabled: bool,
) -> None:
    # `processed_files` lives in one code location; an unconditioned check on it
    # (`external_non_null`) lives in a *different* location. When `processed_files` is
    # requested by an automation tick and no check is individually requested, the run for
    # `processed_files` must NOT attach the other-location check: that check is not part of
    # this location's implicit asset job, so selecting it would make the run un-submittable.
    time = get_current_datetime()
    with (
        _resolve_check_keys_gate(gate_enabled),
        get_workspace_request_context(
            ["cross_location_unconditioned_check_asset", "cross_location_unconditioned_check"]
        ) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)
            # nothing yet -- parent hasn't updated
            assert _get_runs_for_latest_ticks(context) == []

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # update the parent so `processed_files` (eager) is requested with no check
            context.instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=dg.AssetKey("raw_files"))
            )
            _execute_ticks(context, executor)

            runs = _get_runs_for_latest_ticks(context)
            # `external_non_null` has no automation condition, so it is never individually
            # requested; the only run produced is for `processed_files` in its own location.
            assert len(runs) == 1
            run = runs[0]
            assert run.asset_selection == {dg.AssetKey("processed_files")}
            # the other-location check must not be attached to this location's run
            assert (run.asset_check_selection or set()) == set()


def test_default_condition() -> None:
    time = datetime.datetime(2024, 8, 16, 4)
    with (
        get_workspace_request_context(["default_condition"]) as context,
        get_threadpool_executor() as executor,
    ):
        with freeze_time(time):
            _execute_ticks(context, executor)

            # eager asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {dg.AssetKey("eager_asset")}

        time += datetime.timedelta(seconds=60)
        with freeze_time(time):
            _execute_ticks(context, executor)

            # passed a cron tick, so cron asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {dg.AssetKey("every_5_minutes_asset")}


def test_non_subsettable_check() -> None:
    with (
        get_grpc_workspace_request_context("check_not_subsettable") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 17, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)

            # eager asset materializes
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 3

            # unpartitioned
            unpartitioned_run = runs[2]
            assert unpartitioned_run.tags.get("dagster/partition") is None
            assert unpartitioned_run.asset_selection == {dg.AssetKey("unpartitioned")}
            assert unpartitioned_run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("unpartitioned"), name="row_count")
            }

            # static partitioned
            static_partitioned_run = runs[1]
            assert static_partitioned_run.tags.get("dagster/partition") == "a"
            assert static_partitioned_run.asset_selection == {dg.AssetKey("static")}
            assert static_partitioned_run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("static"), name="c1"),
                dg.AssetCheckKey(dg.AssetKey("static"), name="c2"),
            }

            # multi-asset time partitioned
            time_partitioned_run = runs[0]
            assert time_partitioned_run.tags.get("dagster/partition") == "2024-08-16"
            assert time_partitioned_run.asset_selection == {
                dg.AssetKey("a"),
                dg.AssetKey("b"),
                dg.AssetKey("c"),
                dg.AssetKey("d"),
            }
            assert time_partitioned_run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("a"), name="1"),
                dg.AssetCheckKey(dg.AssetKey("a"), name="2"),
                dg.AssetCheckKey(dg.AssetKey("d"), name="3"),
            }


def _get_subsets_by_key(
    backfill: PartitionBackfill, asset_graph: BaseAssetGraph
) -> Mapping[dg.AssetKey, SerializableEntitySubset[dg.AssetKey]]:
    assert backfill.asset_backfill_data is not None
    target_subset = backfill.asset_backfill_data.target_subset
    return {s.key: s for s in target_subset.iterate_asset_subsets()}


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
            _execute_ticks(context, executor)
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {
                dg.AssetKey("A"),
                dg.AssetKey("B"),
                dg.AssetKey("C"),
                dg.AssetKey("D"),
                dg.AssetKey("E"),
            }

            assert subsets_by_key[dg.AssetKey("A")].size == 1
            assert subsets_by_key[dg.AssetKey("B")].size == 3
            assert subsets_by_key[dg.AssetKey("C")].size == 3
            assert subsets_by_key[dg.AssetKey("D")].size == 3
            assert subsets_by_key[dg.AssetKey("E")].size == 1

            # don't create runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # second tick, don't kick off again
            _execute_ticks(context, executor)
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0
            # still don't create runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_backfill_creation_dynamic() -> None:
    with (
        get_grpc_workspace_request_context("backfill_dynamic_user_code") as context,
        get_threadpool_executor() as executor,
    ):
        context.instance.add_dynamic_partitions("dynamic1", ["a", "b", "c"])

        asset_graph = context.create_request_context().asset_graph

        # all start off missing, should be requested
        time = get_current_datetime()
        with freeze_time(time):
            _execute_ticks(context, executor)
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {
                dg.AssetKey("A"),
            }

            with partition_loading_context(dynamic_partitions_store=context.instance):
                assert subsets_by_key[dg.AssetKey("A")].size == 3

            # don't create runs
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
        context.instance.report_runless_asset_event(dg.AssetMaterialization("run2", partition="x"))
        context.instance.report_runless_asset_event(dg.AssetMaterialization("run2", partition="y"))

        # all start off missing, should be requested
        time = get_current_datetime()
        with freeze_time(time):
            _execute_ticks(context, executor)
            # create a backfill for the part of the graph that has multiple partitions
            # required
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 1
            subsets_by_key = _get_subsets_by_key(backfills[0], asset_graph)
            assert subsets_by_key.keys() == {
                dg.AssetKey("backfillA"),
                dg.AssetKey("backfillB"),
                dg.AssetKey("backfillC"),
            }

            assert subsets_by_key[dg.AssetKey("backfillA")].size == 1
            assert subsets_by_key[dg.AssetKey("backfillB")].size == 3
            assert subsets_by_key[dg.AssetKey("backfillC")].size == 3

            # create 2 individual runs
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 2

            # unpartitioned
            unpartitioned_run = runs[0]
            assert unpartitioned_run.tags.get("dagster/partition") is None
            assert unpartitioned_run.asset_selection == {dg.AssetKey("run1")}
            assert unpartitioned_run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("run1"), name="inside")
            }

            # static partitioned 1
            static_partitioned_run = runs[1]
            assert static_partitioned_run.tags.get("dagster/partition") == "z"
            assert static_partitioned_run.asset_selection == {dg.AssetKey("run2")}
            assert static_partitioned_run.asset_check_selection == {
                dg.AssetCheckKey(dg.AssetKey("run2"), name="inside")
            }

        time += datetime.timedelta(seconds=30)
        with freeze_time(time):
            # second tick, don't kick off again
            _execute_ticks(context, executor)

            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_toggle_user_code() -> None:
    with (
        dg.instance_for_test(
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
                    _execute_ticks(context, executor)
                    runs = _get_runs_for_latest_ticks(context)
                    assert len(runs) == 0

                time += datetime.timedelta(seconds=35)
                with freeze_time(time):
                    # second tick, root gets updated
                    instance.report_runless_asset_event(dg.AssetMaterialization("root"))
                    _execute_ticks(context, executor)
                    runs = _get_runs_for_latest_ticks(context)
                    assert runs[0].asset_selection == {dg.AssetKey("downstream")}

                time += datetime.timedelta(seconds=35)
                with freeze_time(time):
                    # third tick, don't kick off again
                    _execute_ticks(context, executor)
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
                _execute_ticks(context, executor)
                runs = _get_runs_for_latest_ticks(context)
                assert len(runs) == 0
            time += datetime.timedelta(minutes=1)

        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1

        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_500_eager_assets_user_code(capsys) -> None:
    with (
        get_grpc_workspace_request_context("500_eager_assets") as context,
        get_threadpool_executor() as executor,
    ):
        # The gRPC child process uses real wall-clock time (freeze_time only patches
        # the host process), so both must be in the same hour to see the same set of
        # hourly partitions. If real time crosses an hour boundary mid-test, the gRPC
        # process sees a new partition the host doesn't, causing `newly_missing` to
        # fire and unexpected runs to be created.
        #
        # The test takes ~70s of real time. If we're within 2 min of the next
        # hour, sleep past the boundary so the real clock stays in one hour throughout.
        now = datetime.datetime.now()
        seconds_until_next_hour = (59 - now.minute) * 60 + (60 - now.second)
        if seconds_until_next_hour < 120:
            time.sleep(seconds_until_next_hour + 5)
            now = datetime.datetime.now()
        freeze_dt = now.replace(minute=30, second=0, microsecond=0)

        for _ in range(2):
            clock_time = time.time()
            with freeze_time(freeze_dt):
                _execute_ticks(context, executor)
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
        _execute_ticks(context, executor)
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
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1


def test_observable_source_asset() -> None:
    with (
        get_grpc_workspace_request_context("hourly_observable") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        time += datetime.timedelta(hours=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {dg.AssetKey("obs")}

        # runs haven't completed yet
        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0


def test_observable_source_asset_is_not_backfilled() -> None:
    with (
        get_grpc_workspace_request_context("hourly_observable_with_partitions") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0

        time += datetime.timedelta(hours=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 3
            assert all(run.asset_selection == {dg.AssetKey("obs")} for run in runs)
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0

        # runs haven't completed yet
        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0
            backfills = _get_backfills_for_latest_ticks(context)
            assert len(backfills) == 0


def test_dynamic_partitions() -> None:
    with (
        get_grpc_workspace_request_context("dynamic_partitions_on_missing") as context,
        get_threadpool_executor() as executor,
    ):
        time = datetime.datetime(2024, 8, 16, 1, 35)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        context.instance.add_dynamic_partitions("dynamic", ["a", "b", "c"])
        context.instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="a"))
        context.instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="b"))

        time += datetime.timedelta(hours=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1
            assert runs[0].asset_selection == {dg.AssetKey("A")}
            assert runs[0].tags["dagster/partition"] == "c"

        time += datetime.timedelta(minutes=1)
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0

        # add new partition
        time += datetime.timedelta(minutes=1)
        context.instance.add_dynamic_partitions("dynamic", ["d"])
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 1

        # delete a partition that we just added, should not cause errors
        time += datetime.timedelta(minutes=1)
        context.instance.delete_dynamic_partition("dynamic", "d")
        with freeze_time(time):
            _execute_ticks(context, executor)
            runs = _get_runs_for_latest_ticks(context)
            assert len(runs) == 0
