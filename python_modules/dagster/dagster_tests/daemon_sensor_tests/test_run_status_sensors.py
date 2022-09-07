import tempfile
import time
from contextlib import contextmanager

import pendulum
import pytest

from dagster import DagsterRunStatus
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.storage.event_log.base import EventRecordsFilter
from dagster._core.test_utils import create_test_daemon_workspace, instance_for_test

from .conftest import workspace_load_target
from .test_sensor_run import (
    evaluate_sensors,
    failure_job,
    failure_pipeline,
    foo_pipeline,
    get_sensor_executors,
    hanging_pipeline,
    the_pipeline,
    validate_tick,
    wait_for_all_runs_to_finish,
)


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture():
    # Overridden from conftest.py, uses DefaultRunLauncher since we care about
    # runs actually completing for run status sensors
    with instance_for_test(
        overrides={},
    ) as instance:
        yield instance


@contextmanager
def instance_with_sensors(overrides=None, attribute="the_repo"):
    with instance_for_test(overrides=overrides) as instance:
        with create_test_daemon_workspace(
            workspace_load_target(attribute=attribute), instance=instance
        ) as workspace:
            yield (
                instance,
                workspace,
                next(
                    iter(workspace.get_workspace_snapshot().values())
                ).repository_location.get_repository(attribute),
            )


@contextmanager
def instance_with_multiple_repos_with_sensors(overrides=None):
    with instance_for_test(overrides) as instance:
        with create_test_daemon_workspace(
            workspace_load_target(None), instance=instance
        ) as workspace:
            yield (
                instance,
                workspace,
                next(
                    iter(workspace.get_workspace_snapshot().values())
                ).repository_location.get_repositories(),
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_status_sensor(caplog, executor, instance, workspace, external_repo):
    freeze_datetime = pendulum.now()
    with pendulum.test(freeze_datetime):
        success_sensor = external_repo.get_external_sensor("my_pipeline_success_sensor")
        instance.start_sensor(success_sensor)

        started_sensor = external_repo.get_external_sensor("my_pipeline_started_sensor")
        instance.start_sensor(started_sensor)

        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            success_sensor.get_external_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
        time.sleep(1)

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
        run = instance.create_run_for_pipeline(
            failure_pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):

        # should not fire the success sensor, should fire the started sensro
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            success_sensor.get_external_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        ticks = instance.get_ticks(
            started_sensor.get_external_origin_id(), started_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            started_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("foo_pipeline")
        run = instance.create_run_for_pipeline(
            foo_pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.SUCCESS
        freeze_datetime = freeze_datetime.add(seconds=60)

    caplog.clear()

    with pendulum.test(freeze_datetime):

        # should fire the success sensor and the started sensor
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            success_sensor.get_external_origin_id(), success_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            success_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

        ticks = instance.get_ticks(
            started_sensor.get_external_origin_id(), started_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            started_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

        assert (
            'Sensor "my_pipeline_started_sensor" acted on run status STARTED of run' in caplog.text
        )
        assert (
            'Sensor "my_pipeline_success_sensor" acted on run status SUCCESS of run' in caplog.text
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_failure_sensor(executor, instance, workspace, external_repo):
    freeze_datetime = pendulum.now()
    with pendulum.test(freeze_datetime):
        failure_sensor = external_repo.get_external_sensor("my_run_failure_sensor")
        instance.start_sensor(failure_sensor)

        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
        time.sleep(1)

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
        run = instance.create_run_for_pipeline(
            failure_pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):

        # should fire the failure sensor
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_failure_sensor_that_fails(executor, instance, workspace, external_repo):
    freeze_datetime = pendulum.now()
    with pendulum.test(freeze_datetime):
        failure_sensor = external_repo.get_external_sensor(
            "my_run_failure_sensor_that_itself_fails"
        )
        instance.start_sensor(failure_sensor)

        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
        time.sleep(1)

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
        run = instance.create_run_for_pipeline(
            failure_pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):

        # should fire the failure sensor and fail
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
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
    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should fire the failure sensor and fail
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_failure_sensor_filtered(executor, instance, workspace, external_repo):
    freeze_datetime = pendulum.now()
    with pendulum.test(freeze_datetime):
        failure_sensor = external_repo.get_external_sensor("my_run_failure_sensor_filtered")
        instance.start_sensor(failure_sensor)

        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
        time.sleep(1)

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
        run = instance.create_run_for_pipeline(
            failure_pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE
        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):

        # should not fire the failure sensor (filtered to failure job)
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
        time.sleep(1)

    with pendulum.test(freeze_datetime):
        external_pipeline = external_repo.get_full_external_pipeline("failure_graph")
        run = instance.create_run_for_pipeline(
            failure_job,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )
        instance.submit_run(run.run_id, workspace)
        wait_for_all_runs_to_finish(instance)
        run = instance.get_runs()[0]
        assert run.status == DagsterRunStatus.FAILURE

        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):

        # should not fire the failure sensor (filtered to failure job)
        evaluate_sensors(instance, workspace, executor)

        ticks = instance.get_ticks(
            failure_sensor.get_external_origin_id(), failure_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            failure_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )


def sqlite_storage_config_fn(temp_dir):
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


def sql_event_log_storage_config_fn(temp_dir):
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
@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_status_sensor_interleave(storage_config_fn, executor):
    freeze_datetime = pendulum.now()
    with tempfile.TemporaryDirectory() as temp_dir:

        with instance_with_sensors(overrides=storage_config_fn(temp_dir)) as (
            instance,
            workspace,
            external_repo,
        ):
            # start sensor
            with pendulum.test(freeze_datetime):
                failure_sensor = external_repo.get_external_sensor("my_run_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_external_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            with pendulum.test(freeze_datetime):
                external_pipeline = external_repo.get_full_external_pipeline("hanging_pipeline")
                # start run 1
                run1 = instance.create_run_for_pipeline(
                    hanging_pipeline,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                instance.submit_run(run1.run_id, workspace)
                freeze_datetime = freeze_datetime.add(seconds=60)
                # start run 2
                run2 = instance.create_run_for_pipeline(
                    hanging_pipeline,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                instance.submit_run(run2.run_id, workspace)
                freeze_datetime = freeze_datetime.add(seconds=60)
                # fail run 2
                instance.report_run_failed(run2)
                freeze_datetime = freeze_datetime.add(seconds=60)
                run = instance.get_runs()[0]
                assert run.status == DagsterRunStatus.FAILURE
                assert run.run_id == run2.run_id

            # check sensor
            with pendulum.test(freeze_datetime):

                # should fire for run 2
                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_external_origin_id(), failure_sensor.selector_id
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
            with pendulum.test(freeze_datetime):
                # fail run 2
                instance.report_run_failed(run1)
                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            # check sensor
            with pendulum.test(freeze_datetime):

                # should fire for run 1
                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_external_origin_id(), failure_sensor.selector_id
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
@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_failure_sensor_empty_run_records(storage_config_fn, executor):
    freeze_datetime = pendulum.now()
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_with_sensors(overrides=storage_config_fn(temp_dir)) as (
            instance,
            workspace,
            external_repo,
        ):
            with pendulum.test(freeze_datetime):
                failure_sensor = external_repo.get_external_sensor("my_run_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_external_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            with pendulum.test(freeze_datetime):
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
                failure_events = instance.get_event_records(
                    EventRecordsFilter(event_type=DagsterEventType.PIPELINE_FAILURE)
                )
                assert len(failure_events) == 1
                freeze_datetime = freeze_datetime.add(seconds=60)

            with pendulum.test(freeze_datetime):
                # shouldn't fire the failure sensor due to the mismatch
                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    failure_sensor.get_external_origin_id(), failure_sensor.selector_id
                )
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_cross_repo_run_status_sensor(executor):
    freeze_datetime = pendulum.now()
    with instance_with_multiple_repos_with_sensors() as (
        instance,
        workspace,
        repos,
    ):
        the_repo = repos["the_repo"]
        the_other_repo = repos["the_other_repo"]

        with pendulum.test(freeze_datetime):
            cross_repo_sensor = the_repo.get_external_sensor("cross_repo_sensor")
            instance.start_sensor(cross_repo_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = the_other_repo.get_full_external_pipeline("the_pipeline")
            run = instance.create_run_for_pipeline(
                the_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_cross_repo_job_run_status_sensor(executor):
    freeze_datetime = pendulum.now()
    with instance_with_multiple_repos_with_sensors() as (
        instance,
        workspace,
        repos,
    ):
        the_repo = repos["the_repo"]
        the_other_repo = repos["the_other_repo"]

        with pendulum.test(freeze_datetime):
            cross_repo_sensor = the_repo.get_external_sensor("cross_repo_job_sensor")
            instance.start_sensor(cross_repo_sensor)

            assert instance.get_runs_count() == 0

            evaluate_sensors(instance, workspace, executor)
            wait_for_all_runs_to_finish(instance)
            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(
                cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = the_other_repo.get_full_external_pipeline("the_pipeline")
            run = instance.create_run_for_pipeline(
                the_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            assert run.status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace, executor)
            wait_for_all_runs_to_finish(instance)

            ticks = instance.get_ticks(
                cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "the_graph"]
            assert len(run_request_runs) == 1
            assert run_request_runs[0].status == DagsterRunStatus.SUCCESS
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):
            # ensure that the success of the run launched by the sensor doesn't trigger the sensor
            evaluate_sensors(instance, workspace, executor)
            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "the_graph"]
            assert len(run_request_runs) == 1

            ticks = instance.get_ticks(
                cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
            )
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                cross_repo_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_different_instance_run_status_sensor(executor):
    freeze_datetime = pendulum.now()
    with instance_with_sensors() as (
        instance,
        workspace,
        the_repo,
    ):
        with instance_with_sensors(attribute="the_other_repo") as (
            the_other_instance,
            the_other_workspace,
            the_other_repo,
        ):

            with pendulum.test(freeze_datetime):
                cross_repo_sensor = the_repo.get_external_sensor("cross_repo_sensor")
                instance.start_sensor(cross_repo_sensor)

                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
                )
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    cross_repo_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            with pendulum.test(freeze_datetime):
                external_pipeline = the_other_repo.get_full_external_pipeline("the_pipeline")
                run = the_other_instance.create_run_for_pipeline(
                    the_pipeline,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                the_other_instance.submit_run(run.run_id, the_other_workspace)
                wait_for_all_runs_to_finish(the_other_instance)
                run = the_other_instance.get_runs()[0]
                assert run.status == DagsterRunStatus.SUCCESS
                freeze_datetime = freeze_datetime.add(seconds=60)

            with pendulum.test(freeze_datetime):

                evaluate_sensors(instance, workspace, executor)

                ticks = instance.get_ticks(
                    cross_repo_sensor.get_external_origin_id(), cross_repo_sensor.selector_id
                )
                assert len(ticks) == 2
                # the_pipeline was run in another instance, so the cross_repo_sensor should not trigger
                validate_tick(
                    ticks[0],
                    cross_repo_sensor,
                    freeze_datetime,
                    TickStatus.SKIPPED,
                )
