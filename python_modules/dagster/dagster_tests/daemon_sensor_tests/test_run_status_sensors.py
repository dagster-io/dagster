import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Mapping, NamedTuple, Optional, Tuple, cast

import pytest
from dagster import (
    DagsterRunStatus,
    _check as check,
    file_relative_path,
)
from dagster._core.definitions.instigation_logger import get_instigation_log_records
from dagster._core.definitions.run_status_sensor_definition import RunStatusSensorCursor
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR
from dagster._core.remote_representation import CodeLocation, RemoteRepository
from dagster._core.scheduler.instigation import SensorInstigatorData, TickStatus
from dagster._core.test_utils import (
    create_test_daemon_workspace_context,
    environ,
    freeze_time,
    instance_for_test,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import WorkspaceFileTarget, WorkspaceLoadTarget
from dagster._serdes.serdes import deserialize_value
from dagster._time import get_current_datetime
from dagster._vendored.dateutil.relativedelta import relativedelta

from dagster_tests.daemon_sensor_tests.conftest import create_workspace_load_target
from dagster_tests.daemon_sensor_tests.test_sensor_run import (
    daily_partitioned_job,
    evaluate_sensors,
    failure_job,
    failure_job_2,
    foo_job,
    hanging_job,
    the_job,
    validate_tick,
    wait_for_all_runs_to_finish,
)


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture() -> Iterator[DagsterInstance]:
    # Overridden from conftest.py, uses DefaultRunLauncher since we care about
    # runs actually completing for run status sensors
    with instance_for_test(
        overrides={},
    ) as instance:
        yield instance


@contextmanager
def instance_with_sensors(overrides=None, attribute="the_repo"):
    with instance_for_test(overrides=overrides) as instance:
        with create_test_daemon_workspace_context(
            create_workspace_load_target(attribute=attribute), instance=instance
        ) as workspace_context:
            yield (
                instance,
                workspace_context,
                check.not_none(
                    next(
                        iter(
                            workspace_context.create_request_context()
                            .get_code_location_entries()
                            .values()
                        )
                    ).code_location
                ).get_repository(attribute),
            )


class CodeLocationInfoForSensorTest(NamedTuple):
    instance: DagsterInstance
    context: WorkspaceProcessContext
    repositories: Dict[str, RemoteRepository]
    code_location: CodeLocation

    def get_single_repository(self) -> RemoteRepository:
        assert len(self.repositories) == 1
        return next(iter(self.repositories.values()))


@contextmanager
def instance_with_single_code_location_multiple_repos_with_sensors(
    overrides: Optional[Mapping[str, Any]] = None,
    workspace_load_target: Optional[WorkspaceLoadTarget] = None,
) -> Iterator[Tuple[DagsterInstance, WorkspaceProcessContext, Dict[str, RemoteRepository]]]:
    with instance_with_multiple_code_locations(overrides, workspace_load_target) as many_tuples:
        assert len(many_tuples) == 1
        location_info = next(iter(many_tuples.values()))
        yield (
            location_info.instance,
            location_info.context,
            location_info.repositories,
        )


@contextmanager
def instance_with_multiple_code_locations(
    overrides: Optional[Mapping[str, Any]] = None, workspace_load_target=None
) -> Iterator[Dict[str, CodeLocationInfoForSensorTest]]:
    with instance_for_test(overrides) as instance:
        with create_test_daemon_workspace_context(
            workspace_load_target or create_workspace_load_target(None), instance=instance
        ) as workspace_context:
            location_infos: Dict[str, CodeLocationInfoForSensorTest] = {}

            for code_location_entry in (
                workspace_context.create_request_context().get_code_location_entries().values()
            ):
                code_location: CodeLocation = check.not_none(code_location_entry.code_location)
                location_infos[code_location.name] = CodeLocationInfoForSensorTest(
                    instance=instance,
                    context=workspace_context,
                    repositories={**code_location.get_repositories()},
                    code_location=code_location,
                )

            yield location_infos


def test_run_status_sensor(
    caplog,
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        success_sensor = external_repo.get_sensor("my_job_success_sensor")
        instance.start_sensor(success_sensor)

        started_sensor = external_repo.get_sensor("my_job_started_sensor")
        instance.start_sensor(started_sensor)

        state = instance.get_instigator_state(
            started_sensor.get_remote_origin_id(), started_sensor.selector_id
        )
        assert (
            cast(SensorInstigatorData, check.not_none(state).instigator_data).sensor_type
            == SensorType.RUN_STATUS
        )

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("failure_job")
        run = instance.create_run_for_job(
            failure_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should not fire the success sensor, should fire the started sensro
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        ticks = instance.get_ticks(
            started_sensor.get_remote_origin_id(), started_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            started_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("foo_job")
        run = instance.create_run_for_job(
            foo_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.SUCCESS
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    caplog.clear()

    with freeze_time(freeze_datetime):
        # should fire the success sensor and the started sensor
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

        ticks = instance.get_ticks(
            started_sensor.get_remote_origin_id(), started_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            started_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

        assert 'Sensor "my_job_started_sensor" acted on run status STARTED of run' in caplog.text
        assert 'Sensor "my_job_success_sensor" acted on run status SUCCESS of run' in caplog.text


def test_run_failure_sensor(
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        failure_sensor = external_repo.get_sensor("my_run_failure_sensor")
        instance.start_sensor(failure_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("failure_job")
        run = instance.create_run_for_job(
            failure_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should fire the failure sensor
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )


def test_run_failure_sensor_that_fails(
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        failure_sensor = external_repo.get_sensor("my_run_failure_sensor_that_itself_fails")
        instance.start_sensor(failure_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("failure_job")
        run = instance.create_run_for_job(
            failure_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should fire the failure sensor and fail
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            expected_error="How meta",
        )

    # Next tick skips again
    freeze_datetime = freeze_datetime + relativedelta(seconds=60)
    with freeze_time(freeze_datetime):
        # should fire the failure sensor and fail
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )


def test_run_failure_sensor_filtered(
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        failure_sensor = external_repo.get_sensor("my_run_failure_sensor_filtered")
        instance.start_sensor(failure_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("failure_job_2")
        run = instance.create_run_for_job(
            failure_job_2,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should not fire the failure sensor (filtered to failure job)
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("failure_job")
        run = instance.create_run_for_job(
            failure_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should not fire the failure sensor (filtered to failure job)
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )


def test_run_failure_sensor_overfetch(
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    external_repo: RemoteRepository,
):
    with environ(
        {
            "DAGSTER_RUN_STATUS_SENSOR_FETCH_LIMIT": "6",
            "DAGSTER_RUN_STATUS_SENSOR_PROCESS_LIMIT": "2",
        },
    ):
        with create_test_daemon_workspace_context(
            workspace_load_target=create_workspace_load_target(), instance=instance
        ) as workspace_context:
            freeze_datetime = get_current_datetime()
            with freeze_time(freeze_datetime):
                failure_sensor = external_repo.get_sensor("my_run_failure_sensor_filtered")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                time.sleep(1)

            with freeze_time(freeze_datetime):
                matching_runs = []
                non_matching_runs = []

                # interleave matching jobs and jobs that do not match
                for _i in range(4):
                    remote_job = external_repo.get_full_job("failure_job")
                    remote_job_2 = external_repo.get_full_job("failure_job_2")

                    run = instance.create_run_for_job(
                        failure_job_2,
                        remote_job_origin=remote_job_2.get_remote_origin(),
                        job_code_origin=remote_job_2.get_python_origin(),
                    )
                    instance.report_run_failed(run)

                    non_matching_runs.append(run)

                    run = instance.create_run_for_job(
                        failure_job,
                        remote_job_origin=remote_job.get_remote_origin(),
                        job_code_origin=remote_job.get_python_origin(),
                    )
                    instance.report_run_failed(run)

                    matching_runs.append(run)

                freeze_datetime = freeze_datetime + relativedelta(seconds=60)

            with freeze_time(freeze_datetime):
                # should fire the failure sensor (filtered to failure job)
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SUCCESS,
                )

                assert set(ticks[0].origin_run_ids or []) == {
                    matching_runs[0].run_id,
                    matching_runs[1].run_id,
                }

                # Additional non-matching run was incorporated into the cursor

                run_status_changes = instance.event_log_storage.fetch_run_status_changes(
                    records_filter=DagsterEventType.RUN_FAILURE, ascending=True, limit=1000
                )
                assert len(run_status_changes.records) == 8

                last_non_matching_run_storage_records = [
                    record
                    for record in run_status_changes.records
                    if record.run_id == non_matching_runs[2].run_id
                ]
                assert len(last_non_matching_run_storage_records) == 1

                assert (
                    deserialize_value(
                        check.not_none(ticks[0].cursor), RunStatusSensorCursor
                    ).record_id
                    == last_non_matching_run_storage_records[0].storage_id
                )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            with freeze_time(freeze_datetime):
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 3
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SUCCESS,
                )

                assert set(ticks[0].origin_run_ids or []) == {
                    matching_runs[2].run_id,
                    matching_runs[3].run_id,
                }

                last_matching_run_storage_records = [
                    record
                    for record in run_status_changes.records
                    if record.run_id == matching_runs[3].run_id
                ]
                assert len(last_matching_run_storage_records) == 1

                assert (
                    deserialize_value(
                        check.not_none(ticks[0].cursor), RunStatusSensorCursor
                    ).record_id
                    == last_matching_run_storage_records[0].storage_id
                )


def sqlite_storage_config_fn(temp_dir: str) -> Dict[str, Any]:
    # non-run sharded storage
    return {
        "run_storage": {
            "module": "dagster._core.storage.runs",
            "class": "SqliteRunStorage",
            "config": {"base_dir": temp_dir},
        },
        "event_log_storage": {
            "module": "dagster._core.storage.event_log",
            "class": "SqliteEventLogStorage",
            "config": {"base_dir": temp_dir},
        },
    }


def default_storage_config_fn(_):
    # run sharded storage
    return {}


def sql_event_log_storage_config_fn(temp_dir: str):
    return {
        "event_log_storage": {
            "module": "dagster._core.storage.event_log",
            "class": "ConsolidatedSqliteEventLogStorage",
            "config": {"base_dir": temp_dir},
        },
    }


@pytest.mark.parametrize(
    "storage_config_fn",
    [default_storage_config_fn, sqlite_storage_config_fn],
)
def test_run_status_sensor_interleave(storage_config_fn, executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_with_sensors(overrides=storage_config_fn(temp_dir)) as (
            instance,
            workspace_context,
            external_repo,
        ):
            # start sensor
            with freeze_time(freeze_datetime):
                failure_sensor = external_repo.get_sensor("my_run_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                time.sleep(1)

            with freeze_time(freeze_datetime):
                remote_job = external_repo.get_full_job("hanging_job")
                # start run 1
                run1 = instance.create_run_for_job(
                    hanging_job,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )
                instance.submit_run(run1.run_id, workspace_context.create_request_context())
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                # start run 2
                run2 = instance.create_run_for_job(
                    hanging_job,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )
                instance.submit_run(run2.run_id, workspace_context.create_request_context())
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                # fail run 2
                instance.report_run_failed(run2)
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                run = instance.get_runs()[0]
                assert run.status == DagsterRunStatus.FAILURE
                assert run.run_id == run2.run_id

            # check sensor
            with freeze_time(freeze_datetime):
                # should fire for run 2
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SUCCESS,
                )
                assert len(ticks[0].origin_run_ids) == 1
                assert ticks[0].origin_run_ids[0] == run2.run_id

            # fail run 1
            with freeze_time(freeze_datetime):
                # fail run 2
                instance.report_run_failed(run1)
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                time.sleep(1)

            # check sensor
            with freeze_time(freeze_datetime):
                # should fire for run 1
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 3
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SUCCESS,
                )
                assert len(ticks[0].origin_run_ids) == 1
                assert ticks[0].origin_run_ids[0] == run1.run_id


@pytest.mark.parametrize("storage_config_fn", [sql_event_log_storage_config_fn])
def test_run_failure_sensor_empty_run_records(
    storage_config_fn, executor: Optional[ThreadPoolExecutor]
):
    freeze_datetime = get_current_datetime()
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_with_sensors(overrides=storage_config_fn(temp_dir)) as (
            instance,
            workspace_context,
            external_repo,
        ):
            with freeze_time(freeze_datetime):
                failure_sensor = external_repo.get_sensor("my_run_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                time.sleep(1)

            with freeze_time(freeze_datetime):
                # create a mismatch between event storage and run storage
                instance.event_log_storage.store_event(
                    EventLogEntry(
                        error_info=None,
                        level="debug",
                        user_message="",
                        run_id="fake_run_id",
                        timestamp=time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.PIPELINE_FAILURE.value,
                            "foo",
                        ),
                    )
                )
                runs = instance.get_runs()
                assert len(runs) == 0
                failure_events = instance.fetch_run_status_changes(
                    DagsterEventType.PIPELINE_FAILURE, limit=5000
                ).records
                assert len(failure_events) == 1
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)

            with freeze_time(freeze_datetime):
                # shouldn't fire the failure sensor due to the mismatch
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_remote_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )


def test_all_code_locations_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()

    # we have no good api for compositing load targets so forced to use a workspace file
    workspace_load_target = WorkspaceFileTarget(
        [file_relative_path(__file__, "daemon_sensor_defs_test_workspace.yaml")]
    )

    # the name of the location by default is the fully-qualified module name
    daemon_sensor_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.daemon_sensor_defs"
    )
    job_defs_name = "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs"

    with instance_with_multiple_code_locations(
        workspace_load_target=workspace_load_target
    ) as location_infos:
        assert len(location_infos) == 2

        daemon_sensor_defs_location_info = location_infos[daemon_sensor_defs_name]
        job_defs_location_info = location_infos[job_defs_name]

        sensor_repo = daemon_sensor_defs_location_info.get_single_repository()
        job_repo = job_defs_location_info.get_single_repository()

        # verify assumption that the instances are the same
        assert daemon_sensor_defs_location_info.instance == job_defs_location_info.instance
        instance = daemon_sensor_defs_location_info.instance

        # verify assumption that the contexts are the same
        assert daemon_sensor_defs_location_info.context == job_defs_location_info.context
        workspace_context = daemon_sensor_defs_location_info.context

        # This remainder is largely copied from test_cross_repo_run_status_sensor
        with freeze_time(freeze_datetime):
            my_sensor = sensor_repo.get_sensor("all_code_locations_run_status_sensor")
            instance.start_sensor(my_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = [*instance.get_ticks(my_sensor.get_remote_origin_id(), my_sensor.selector_id)]
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                my_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            external_another_job = job_repo.get_full_job("another_success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                another_success_job,
            )

            dagster_run = instance.create_run_for_job(
                another_success_job,
                remote_job_origin=external_another_job.get_remote_origin(),
                job_code_origin=external_another_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [*instance.get_ticks(my_sensor.get_remote_origin_id(), my_sensor.selector_id)]
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                my_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_all_code_location_run_failure_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()

    # we have no good api for compositing load targets so forced to use a workspace file
    workspace_load_target = WorkspaceFileTarget(
        [file_relative_path(__file__, "daemon_sensor_defs_test_workspace.yaml")]
    )

    # the name of the location by default is the fully-qualified module name
    daemon_sensor_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.daemon_sensor_defs"
    )
    job_defs_name = "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs"

    with instance_with_multiple_code_locations(
        workspace_load_target=workspace_load_target
    ) as location_infos:
        assert len(location_infos) == 2

        daemon_sensor_defs_location_info = location_infos[daemon_sensor_defs_name]
        job_defs_location_info = location_infos[job_defs_name]

        sensor_repo = daemon_sensor_defs_location_info.get_single_repository()
        job_repo = job_defs_location_info.get_single_repository()

        # verify assumption that the instances are the same
        assert daemon_sensor_defs_location_info.instance == job_defs_location_info.instance
        instance = daemon_sensor_defs_location_info.instance

        # verify assumption that the contexts are the same
        assert daemon_sensor_defs_location_info.context == job_defs_location_info.context
        workspace_context = daemon_sensor_defs_location_info.context

        # This remainder is largely copied from test_cross_repo_run_status_sensor
        with freeze_time(freeze_datetime):
            my_sensor = sensor_repo.get_sensor("all_code_locations_run_failure_sensor")
            instance.start_sensor(my_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = [*instance.get_ticks(my_sensor.get_remote_origin_id(), my_sensor.selector_id)]
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                my_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            external_another_job = job_repo.get_full_job("another_failure_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                another_failure_job,
            )

            dagster_run = instance.create_run_for_job(
                another_failure_job,
                remote_job_origin=external_another_job.get_remote_origin(),
                job_code_origin=external_another_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.FAILURE
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [*instance.get_ticks(my_sensor.get_remote_origin_id(), my_sensor.selector_id)]
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                my_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_cross_code_location_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()

    # we have no good api for compositing load targets so forced to use a workspace file
    workspace_load_target = WorkspaceFileTarget(
        [file_relative_path(__file__, "daemon_sensor_defs_test_workspace.yaml")]
    )

    # the name of the location by default is the fully-qualified module name
    daemon_sensor_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.daemon_sensor_defs"
    )
    success_job_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs"
    )

    with instance_with_multiple_code_locations(
        workspace_load_target=workspace_load_target
    ) as location_infos:
        assert len(location_infos) == 2

        daemon_sensor_defs_location_info = location_infos[daemon_sensor_defs_name]
        success_job_def_location_info = location_infos[success_job_defs_name]

        sensor_repo = daemon_sensor_defs_location_info.get_single_repository()
        job_repo = success_job_def_location_info.get_single_repository()

        # verify assumption that the instances are the same
        assert daemon_sensor_defs_location_info.instance == success_job_def_location_info.instance
        instance = daemon_sensor_defs_location_info.instance

        # verify assumption that the contexts are the same
        assert daemon_sensor_defs_location_info.context == success_job_def_location_info.context
        workspace_context = daemon_sensor_defs_location_info.context

        # This remainder is largely copied from test_cross_repo_run_status_sensor
        with freeze_time(freeze_datetime):
            success_sensor = sensor_repo.get_sensor("success_sensor")
            instance.start_sensor(success_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            external_success_job = job_repo.get_full_job("success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                success_job,
            )

            dagster_run = instance.create_run_for_job(
                success_job,
                remote_job_origin=external_success_job.get_remote_origin(),
                job_code_origin=external_success_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_cross_code_location_job_selector_on_defs_run_status_sensor(
    executor: Optional[ThreadPoolExecutor],
):
    freeze_datetime = get_current_datetime()

    # we have no good api for compositing load targets so forced to use a workspace file
    workspace_load_target = WorkspaceFileTarget(
        [file_relative_path(__file__, "daemon_sensor_defs_test_workspace.yaml")]
    )

    # the name of the location by default is the fully-qualified module name
    daemon_sensor_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.daemon_sensor_defs"
    )
    success_job_defs_name = (
        "dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs"
    )

    with instance_with_multiple_code_locations(
        workspace_load_target=workspace_load_target
    ) as location_infos:
        assert len(location_infos) == 2

        daemon_sensor_defs_location_info = location_infos[daemon_sensor_defs_name]
        success_job_def_location_info = location_infos[success_job_defs_name]

        sensor_repo = daemon_sensor_defs_location_info.get_single_repository()
        job_repo = success_job_def_location_info.get_single_repository()

        # verify assumption that the instances are the same
        assert daemon_sensor_defs_location_info.instance == success_job_def_location_info.instance
        instance = daemon_sensor_defs_location_info.instance

        # verify assumption that the contexts are the same
        assert daemon_sensor_defs_location_info.context == success_job_def_location_info.context
        workspace_context = daemon_sensor_defs_location_info.context

        # This remainder is largely copied from test_cross_repo_run_status_sensor
        with freeze_time(freeze_datetime):
            success_sensor = sensor_repo.get_sensor("success_of_another_job_sensor")
            instance.start_sensor(success_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            external_success_job = job_repo.get_full_job("success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                success_job,
            )

            dagster_run = instance.create_run_for_job(
                success_job,
                remote_job_origin=external_success_job.get_remote_origin(),
                job_code_origin=external_success_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]

            # A successful job was launched but not the one we were listening to.
            # So the tick is skipped

            assert len(ticks) == 2

            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

            time.sleep(1)

        # now launch the run that is actually being listened to

        with freeze_time(freeze_datetime):
            external_another_success_job = job_repo.get_full_job("another_success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                another_success_job,
            )

            dagster_run = instance.create_run_for_job(
                another_success_job,
                remote_job_origin=external_another_success_job.get_remote_origin(),
                job_code_origin=external_another_success_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]

            # A successful job was launched and we are listening to it this time
            # so we check for success

            assert len(ticks) == 3

            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_code_location_scoped_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()

    # we have no good api for compositing load targets so forced to use a workspace file
    workspace_load_target = WorkspaceFileTarget(
        [file_relative_path(__file__, "code_location_scoped_test_workspace.yaml")]
    )

    # the name of the location by default is the fully-qualified module name
    code_location_with_sensor_name = "dagster_tests.daemon_sensor_tests.locations_for_code_location_scoped_sensor_test.code_location_with_sensor"
    code_location_with_dupe_job_name = "dagster_tests.daemon_sensor_tests.locations_for_code_location_scoped_sensor_test.code_location_with_duplicate_job_name"

    with instance_with_multiple_code_locations(
        workspace_load_target=workspace_load_target
    ) as location_infos:
        assert len(location_infos) == 2

        code_location_w_sensor_info = location_infos[code_location_with_sensor_name]
        code_location_w_dupe_job_info = location_infos[code_location_with_dupe_job_name]

        sensor_repo = code_location_w_sensor_info.get_single_repository()
        dupe_job_repo = code_location_w_dupe_job_info.get_single_repository()

        # verify assumption that the instances are the same
        assert code_location_w_sensor_info.instance == code_location_w_dupe_job_info.instance
        instance = code_location_w_sensor_info.instance

        # verify assumption that the contexts are the same
        assert code_location_w_sensor_info.context == code_location_w_dupe_job_info.context
        workspace_context = code_location_w_sensor_info.context

        # This remainder is largely copied from test_cross_repo_run_status_sensor
        with freeze_time(freeze_datetime):
            success_sensor = sensor_repo.get_sensor("success_sensor")
            instance.start_sensor(success_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            external_success_job = sensor_repo.get_full_job("success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                success_job,
            )

            dagster_run = instance.create_run_for_job(
                success_job,
                remote_job_origin=external_success_job.get_remote_origin(),
                job_code_origin=external_success_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

        with freeze_time(freeze_datetime):
            external_success_job = dupe_job_repo.get_full_job("success_job")

            # this unfortunate API (create_run_for_job) requires the importation
            # of the in-memory job object even though it is dealing mostly with
            # "external" objects
            from dagster_tests.daemon_sensor_tests.locations_for_xlocation_sensor_test.job_defs import (
                success_job,
            )

            dagster_run = instance.create_run_for_job(
                success_job,
                remote_job_origin=external_success_job.get_remote_origin(),
                job_code_origin=external_success_job.get_python_origin(),
            )

            instance.submit_run(dagster_run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            dagster_run = next(iter(instance.get_runs()))
            assert dagster_run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = [
                *instance.get_ticks(
                    success_sensor.get_remote_origin_id(), success_sensor.selector_id
                )
            ]
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


def test_cross_repo_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()
    with instance_with_single_code_location_multiple_repos_with_sensors() as (
        instance,
        workspace_context,
        repos,
    ):
        the_repo = repos["the_repo"]
        the_other_repo = repos["the_other_repo"]

        with freeze_time(freeze_datetime):
            cross_repo_sensor = the_repo.get_sensor("cross_repo_sensor")
            instance.start_sensor(cross_repo_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            remote_job = the_other_repo.get_full_job("the_job")
            run = instance.create_run_for_job(
                the_job,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_cross_repo_job_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()
    with instance_with_single_code_location_multiple_repos_with_sensors() as (
        instance,
        workspace_context,
        repos,
    ):
        the_repo = repos["the_repo"]
        the_other_repo = repos["the_other_repo"]

        with freeze_time(freeze_datetime):
            cross_repo_sensor = the_repo.get_sensor("cross_repo_job_sensor")
            instance.start_sensor(cross_repo_sensor)

            assert instance.get_runs_count() == 0

            evaluate_sensors(workspace_context, executor)
            wait_for_all_runs_to_finish(instance)
            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(
                cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            remote_job = the_other_repo.get_full_job("the_job")
            run = instance.create_run_for_job(
                the_job,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            assert run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)
            wait_for_all_runs_to_finish(instance)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            run_request_runs = [r for r in instance.get_runs() if r.job_name == "the_other_job"]
            assert len(run_request_runs) == 1
            assert run_request_runs[0].status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            # ensure that the success of the run launched by the sensor doesn't trigger the sensor
            evaluate_sensors(workspace_context, executor)
            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.job_name == "the_other_job"]
            assert len(run_request_runs) == 1

            ticks = instance.get_ticks(
                cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


def test_partitioned_job_run_status_sensor(
    caplog,
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        success_sensor = external_repo.get_sensor("partitioned_pipeline_success_sensor")
        instance.start_sensor(success_sensor)

        assert instance.get_runs_count() == 0
        evaluate_sensors(workspace_context, executor)
        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)
        time.sleep(1)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("daily_partitioned_job")
        run = instance.create_run_for_job(
            daily_partitioned_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
            tags={"dagster/partition": "2022-08-01"},
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.SUCCESS
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    caplog.clear()

    with freeze_time(freeze_datetime):
        # should fire the success sensor
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        assert (
            'Sensor "partitioned_pipeline_success_sensor" acted on run status SUCCESS of run'
            in caplog.text
        )


def test_different_instance_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()
    with instance_with_sensors() as (
        instance,
        workspace_context,
        the_repo,
    ):
        with instance_with_sensors(attribute="the_other_repo") as (
            the_other_instance,
            the_other_workspace_context,
            the_other_repo,
        ):
            with freeze_time(freeze_datetime):
                cross_repo_sensor = the_repo.get_sensor("cross_repo_sensor")
                instance.start_sensor(cross_repo_sensor)

                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    cross_repo_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime + relativedelta(seconds=60)
                time.sleep(1)

            with freeze_time(freeze_datetime):
                remote_job = the_other_repo.get_full_job("the_job")
                run = the_other_instance.create_run_for_job(
                    the_job,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )
                the_other_instance.submit_run(
                    run.run_id, the_other_workspace_context.create_request_context()
                )
                wait_for_all_runs_to_finish(the_other_instance)
                run = the_other_instance.get_runs()[0]
                assert run.status == DagsterRunStatus.SUCCESS
                freeze_datetime = freeze_datetime + relativedelta(seconds=60)

            with freeze_time(freeze_datetime):
                evaluate_sensors(workspace_context, executor)

                ticks = instance.get_ticks(
                    cross_repo_sensor.get_remote_origin_id(), cross_repo_sensor.selector_id
                )
                assert len(ticks) == 2
                # the_pipeline was run in another instance, so the cross_repo_sensor should not trigger
                validate_tick(
                    ticks[0],
                    cross_repo_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )


def test_instance_run_status_sensor(executor: Optional[ThreadPoolExecutor]):
    freeze_datetime = get_current_datetime()
    with instance_with_single_code_location_multiple_repos_with_sensors() as (
        instance,
        workspace_context,
        repos,
    ):
        the_repo = repos["the_repo"]
        the_other_repo = repos["the_other_repo"]

        with freeze_time(freeze_datetime):
            instance_sensor = the_repo.get_sensor("instance_sensor")
            instance.start_sensor(instance_sensor)

            evaluate_sensors(workspace_context, executor)

            ticks = instance.get_ticks(
                instance_sensor.get_remote_origin_id(), instance_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                instance_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime + relativedelta(seconds=60)
            time.sleep(1)

        with freeze_time(freeze_datetime):
            remote_job = the_other_repo.get_full_job("the_job")
            run = instance.create_run_for_job(
                the_job,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace_context.create_request_context())
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime + relativedelta(seconds=60)

        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

            ticks = instance.get_ticks(
                instance_sensor.get_remote_origin_id(), instance_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                instance_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


def test_logging_run_status_sensor(
    executor: Optional[ThreadPoolExecutor],
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: RemoteRepository,
):
    freeze_datetime = get_current_datetime()
    with freeze_time(freeze_datetime):
        success_sensor = external_repo.get_sensor("logging_status_sensor")
        instance.start_sensor(success_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        remote_job = external_repo.get_full_job("foo_job")
        run = instance.create_run_for_job(
            foo_job,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace_context.create_request_context())
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.SUCCESS
        freeze_datetime = freeze_datetime + relativedelta(seconds=60)

    with freeze_time(freeze_datetime):
        # should fire the success sensor and the started sensor
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            success_sensor.get_remote_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        tick = ticks[0]
        assert tick.log_key
        records = get_instigation_log_records(instance, tick.log_key)
        assert len(records) == 1
        assert records
        record = records[0]
        assert record[LOG_RECORD_METADATA_ATTR]["orig_message"] == f"run succeeded: {run.run_id}"
        instance.compute_log_manager.delete_logs(log_key=tick.log_key)
