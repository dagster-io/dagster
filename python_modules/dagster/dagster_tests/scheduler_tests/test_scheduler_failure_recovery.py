import pendulum
import pytest
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.job import JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster.core.test_utils import cleanup_test_instance, get_crash_signals, get_terminate_signal
from dagster.scheduler.scheduler import launch_scheduled_runs
from dagster.seven import IS_WINDOWS, multiprocessing

from .test_scheduler_run import (
    instance_with_schedules,
    logger,
    repos,
    validate_run_started,
    validate_tick,
    wait_for_all_runs_to_start,
)


def _test_launch_scheduled_runs_in_subprocess(instance_ref, execution_datetime, debug_crash_flags):
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            with pendulum.test(execution_datetime):
                list(
                    launch_scheduled_runs(
                        instance,
                        logger(),
                        pendulum.now("UTC"),
                        debug_crash_flags=debug_crash_flags,
                    )
                )
        finally:
            cleanup_test_instance(instance)


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize("crash_location", ["TICK_CREATED", "TICK_HELD"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_recovery_before_run_created(
    external_repo_context, crash_location, crash_signal, capfd
):
    # Verify that if the scheduler crashes or is interrupted before a run is created,
    # it will create exactly one tick/run when it is re-launched
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0
        ).in_tz("US/Central")

        frozen_datetime = initial_datetime.add()

        external_schedule = external_repo.get_external_schedule("simple_schedule")
        with pendulum.test(frozen_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            debug_crash_flags = {external_schedule.name: {crash_location: crash_signal}}

            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)

            assert scheduler_process.exitcode != 0

            captured = capfd.readouterr()
            assert (
                captured.out.replace("\r\n", "\n")
                == """2019-02-26 18:00:00 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-26 18:00:00 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at 2019-02-27 00:00:00+0000
"""
            )

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.STARTED

            assert instance.get_runs_count() == 0

        frozen_datetime = frozen_datetime.add(minutes=5)
        with pendulum.test(frozen_datetime):
            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, None],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)
            assert scheduler_process.exitcode == 0

            assert instance.get_runs_count() == 1
            wait_for_all_runs_to_start(instance)
            validate_run_started(
                instance.get_runs()[0],
                execution_time=initial_datetime,
                partition_time=pendulum.datetime(2019, 2, 26),
            )

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [instance.get_runs()[0].run_id],
            )
            captured = capfd.readouterr()
            assert (
                captured.out.replace("\r\n", "\n")
                == """2019-02-26 18:05:00 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-26 18:05:00 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at 2019-02-27 00:00:00+0000
2019-02-26 18:05:00 - SchedulerDaemon - INFO - Resuming previously interrupted schedule execution
2019-02-26 18:05:00 - SchedulerDaemon - INFO - Completed scheduled launch of run {run_id} for simple_schedule
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize("crash_location", ["RUN_CREATED", "RUN_LAUNCHED"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_recovery_after_run_created(
    external_repo_context, crash_location, crash_signal, capfd
):
    # Verify that if the scheduler crashes or is interrupted after a run is created,
    # it will just re-launch the already-created run when it runs again
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        initial_datetime = pendulum.datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        frozen_datetime = initial_datetime.add()
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        with pendulum.test(frozen_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            debug_crash_flags = {external_schedule.name: {crash_location: crash_signal}}

            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)

            assert scheduler_process.exitcode != 0

            capfd.readouterr()

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.STARTED

            assert instance.get_runs_count() == 1

            if crash_location == "RUN_CREATED":
                run = instance.get_runs()[0]
                # Run was created, but hasn't launched yet
                assert run.tags[SCHEDULED_EXECUTION_TIME_TAG] == frozen_datetime.isoformat()
                assert run.tags[PARTITION_NAME_TAG] == "2019-02-26"
                assert run.status == PipelineRunStatus.NOT_STARTED
            else:
                # The run was created and launched - running again should do nothing other than
                # moving the tick to success state.

                # The fact that we need to add this line indicates that there is still a theoretical
                # possible race condition - if the scheduler fails after launching a run
                # and then runs again between when the run was launched and when its status is changed to STARTED by the executor, we could
                # end up launching the same run twice. Run queueing or some other way to immediately
                # identify that a run was launched would help eliminate this race condition. For now,
                # eliminate the possibility by waiting for the run to start before running the
                # scheduler again.
                wait_for_all_runs_to_start(instance)

                run = instance.get_runs()[0]
                validate_run_started(
                    instance.get_runs()[0], frozen_datetime, pendulum.datetime(2019, 2, 26)
                )

                assert run.status in [PipelineRunStatus.STARTED, PipelineRunStatus.SUCCESS]

        frozen_datetime = frozen_datetime.add(minutes=5)
        with pendulum.test(frozen_datetime):

            # Running again just launches the existing run and marks the tick as success
            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, None],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)
            assert scheduler_process.exitcode == 0

            assert instance.get_runs_count() == 1
            wait_for_all_runs_to_start(instance)
            validate_run_started(
                instance.get_runs()[0], initial_datetime, pendulum.datetime(2019, 2, 26)
            )

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [instance.get_runs()[0].run_id],
            )

            captured = capfd.readouterr()
            if crash_location == "RUN_CREATED":
                assert (
                    "Run {run_id} already created for this execution of simple_schedule".format(
                        run_id=instance.get_runs()[0].run_id
                    )
                    in captured.out
                )
            else:
                assert (
                    "Run {run_id} already completed for this execution of simple_schedule".format(
                        run_id=instance.get_runs()[0].run_id
                    )
                    in captured.out
                )


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize("crash_location", ["TICK_SUCCESS"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_recovery_after_tick_success(external_repo_context, crash_location, crash_signal):
    # Verify that if the scheduler crashes or is interrupted after a run is created,
    # it will just re-launch the already-created run when it runs again
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        initial_datetime = pendulum.datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        frozen_datetime = initial_datetime.add()
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        with pendulum.test(frozen_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            debug_crash_flags = {external_schedule.name: {crash_location: crash_signal}}

            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)

            assert scheduler_process.exitcode != 0

            # As above there's a possible race condition here if the scheduler crashes
            # and launches the same run twice if we crash right after the launch and re-run
            # before the run actually starts
            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 1
            validate_run_started(
                instance.get_runs()[0], initial_datetime, pendulum.datetime(2019, 2, 26)
            )

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1

            if crash_signal == get_terminate_signal():
                run_ids = []
            else:
                run_ids = [run.run_id for run in instance.get_runs()]

            validate_tick(
                ticks[0], external_schedule, initial_datetime, JobTickStatus.STARTED, run_ids
            )

        frozen_datetime = frozen_datetime.add(minutes=1)
        with pendulum.test(frozen_datetime):
            # Running again just marks the tick as success since the run has already started
            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, None],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)
            assert scheduler_process.exitcode == 0

            assert instance.get_runs_count() == 1
            validate_run_started(
                instance.get_runs()[0], initial_datetime, pendulum.datetime(2019, 2, 26)
            )

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [instance.get_runs()[0].run_id],
            )


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize("crash_location", ["RUN_ADDED"])
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_failure_recovery_between_multi_runs(external_repo_context, crash_location, crash_signal):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        initial_datetime = pendulum.datetime(year=2019, month=2, day=28, hour=0, minute=0, second=0)
        frozen_datetime = initial_datetime.add()
        external_schedule = external_repo.get_external_schedule("multi_run_schedule")
        with pendulum.test(frozen_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            debug_crash_flags = {external_schedule.name: {crash_location: crash_signal}}

            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, debug_crash_flags],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)

            assert scheduler_process.exitcode != 0

            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            validate_run_started(instance.get_runs()[0], initial_datetime)

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1

        frozen_datetime = frozen_datetime.add(minutes=1)
        with pendulum.test(frozen_datetime):
            scheduler_process = multiprocessing.Process(
                target=_test_launch_scheduled_runs_in_subprocess,
                args=[instance.get_ref(), frozen_datetime, None],
            )
            scheduler_process.start()
            scheduler_process.join(timeout=60)
            assert scheduler_process.exitcode == 0
            assert instance.get_runs_count() == 2
            validate_run_started(instance.get_runs()[0], initial_datetime)
            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )
