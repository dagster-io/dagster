from concurrent.futures import ThreadPoolExecutor

import pendulum
import pytest
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_scheduler_run import (
    evaluate_schedules,
    get_schedule_executors,
    validate_run_started,
    validate_tick,
    wait_for_all_runs_to_start,
)


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_non_utc_timezone_run(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that schedule runs at the expected time in a non-UTC timezone
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 2, 27, 23, 59, 59, tz="US/Central"), "US/Pacific"
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=28, tz="US/Central"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            expected_datetime,
        )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_differing_timezones(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Two schedules, one using US/Central, the other on US/Eastern
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 2, 27, 23, 59, 59, tz="US/Eastern"), "US/Pacific"
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")
        external_eastern_schedule = external_repo.get_external_schedule(
            "daily_eastern_time_schedule"
        )

        schedule_origin = external_schedule.get_external_origin()
        eastern_origin = external_eastern_schedule.get_external_origin()

        instance.start_schedule(external_schedule)
        instance.start_schedule(external_eastern_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        ticks = instance.get_ticks(eastern_origin.get_id(), external_eastern_schedule.selector_id)
        assert len(ticks) == 0

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        ticks = instance.get_ticks(eastern_origin.get_id(), external_eastern_schedule.selector_id)
        assert len(ticks) == 0

    # Past midnight eastern time, the eastern timezone schedule will run, but not the central timezone
    freeze_datetime = freeze_datetime.add(minutes=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(eastern_origin.get_id(), external_eastern_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=28, tz="US/Eastern"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_eastern_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            expected_datetime,
        )

    # Past midnight central time, the central timezone schedule will now run
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(eastern_origin.get_id(), external_eastern_schedule.selector_id)
        assert len(ticks) == 1

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=28, tz="US/Central"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            expected_datetime,
        )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        ticks = instance.get_ticks(eastern_origin.get_id(), external_eastern_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


# Verify that a schedule that runs in US/Central late enough in the day that it executes on
# a different day in UTC still runs and creates its partition names based on the US/Central time
@pytest.mark.parametrize("executor", get_schedule_executors())
def test_different_days_in_different_timezones(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 2, 27, 22, 59, 59, tz="US/Central"), "US/Pacific"
    )
    with pendulum.test(freeze_datetime):
        # Runs every day at 11PM (CST)
        external_schedule = external_repo.get_external_schedule("daily_late_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=27, hour=23, tz="US/Central"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            expected_datetime,
        )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_hourly_dst_spring_forward(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that an hourly schedule still runs hourly during the spring DST transition
    # 1AM CST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 3, 10, 1, 0, 0, tz="US/Central"), "US/Pacific"
    )

    external_schedule = external_repo.get_external_schedule("hourly_central_time_schedule")
    schedule_origin = external_schedule.get_external_origin()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    # DST has now happened, 2 hours later it is 4AM CST
    # Should be 3 runs: 1AM CST, 3AM CST, 4AM CST
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        expected_datetimes_utc = [
            to_timezone(create_pendulum_time(2019, 3, 10, 4, 0, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 10, 3, 0, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 10, 1, 0, 0, tz="US/Central"), "UTC"),
        ]

        for i in range(3):
            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_hourly_dst_fall_back(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that an hourly schedule still runs hourly during the fall DST transition
    # 12:30 AM CST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 11, 3, 0, 30, 0, tz="US/Central"), "US/Pacific"
    )

    external_schedule = external_repo.get_external_schedule("hourly_central_time_schedule")
    schedule_origin = external_schedule.get_external_origin()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0  # 0 because we're on the half-hour
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    for _ in range(3):
        freeze_datetime = freeze_datetime.add(hours=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    # DST has now happened, 4 hours later it is 3:30AM CST
    # Should be 3 runs: 1AM CDT, 2AM CST, 3AM CST
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 3, 9, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 8, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 6, 0, 0, tz="UTC"),
        ]

        expected_ct_times = [
            "2019-11-03T03:00:00-06:00",  # 3 AM CST
            "2019-11-03T02:00:00-06:00",  # 2 AM CST
            "2019-11-03T01:00:00-05:00",  # 1 AM CST
        ]

        for i in range(3):
            assert (
                to_timezone(expected_datetimes_utc[i], "US/Central").isoformat()
                == expected_ct_times[i]
            )

            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_daily_dst_spring_forward(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that a daily schedule still runs once per day during the spring DST transition
    # Night before DST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 3, 10, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")
    schedule_origin = external_schedule.get_external_origin()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        # UTC time changed by one hour after the transition, still running daily at the same
        # time in CT
        expected_datetimes_utc = [
            create_pendulum_time(2019, 3, 12, 5, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 3, 11, 5, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 3, 10, 6, 0, 0, tz="UTC"),
        ]

        for i in range(3):
            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_daily_dst_fall_back(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that a daily schedule still runs once per day during the fall DST transition
    # Night before DST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 11, 3, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        # UTC time changed by one hour after the transition, still running daily at the same
        # time in CT
        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 5, 6, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 4, 6, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 5, 0, 0, tz="UTC"),
        ]

        for i in range(3):
            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_execute_during_dst_transition_spring_forward(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # Verify that a daily schedule that is supposed to execute at a time that is skipped
    # by the DST transition does not execute for that day
    # Day before DST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 3, 9, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule(
            "daily_dst_transition_schedule_skipped_time"
        )
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0  # 0 because we're one the half hour
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    for _ in range(4):
        freeze_datetime = freeze_datetime.add(days=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 5
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 5

        expected_datetimes_utc = [
            to_timezone(create_pendulum_time(2019, 3, 13, 2, 30, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 12, 2, 30, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 11, 2, 30, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 10, 3, 00, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 9, 2, 30, 0, tz="US/Central"), "UTC"),
        ]

        for i in range(5):
            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 5
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 5


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_execute_during_dst_transition_fall_back(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # A schedule that runs daily during a time that occurs twice during a fall DST transition
    # only executes once for that day
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 11, 2, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule(
            "daily_dst_transition_schedule_doubled_time"
        )
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0  # 0 because we're one the half hour
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    for _ in range(2):
        freeze_datetime = freeze_datetime.add(days=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 4, 7, 30, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 7, 30, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 2, 6, 30, 0, tz="UTC"),
        ]

        for i in range(3):
            validate_tick(
                ticks[i],
                external_schedule,
                expected_datetimes_utc[i],
                TickStatus.SUCCESS,
                [instance.get_runs()[i].run_id],
            )

            validate_run_started(
                instance,
                instance.get_runs()[i],
                expected_datetimes_utc[i],
            )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3
