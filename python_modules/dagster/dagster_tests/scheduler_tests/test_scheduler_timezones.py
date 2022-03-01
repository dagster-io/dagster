import pendulum

from dagster.core.scheduler.instigation import TickStatus
from dagster.scheduler.scheduler import launch_scheduled_runs
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster.utils.partitions import DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE

from .test_scheduler_run import (
    logger,
    the_repo,
    validate_run_started,
    validate_tick,
    wait_for_all_runs_to_start,
)


def test_non_utc_timezone_run(instance, workspace, external_repo):
    # Verify that schedule runs at the expected time in a non-UTC timezone
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 2, 27, 23, 59, 59, tz="US/Central"), "US/Pacific"
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
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
            instance.get_runs()[0],
            expected_datetime,
            create_pendulum_time(2019, 2, 27, tz="US/Central"),
        )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


def test_differing_timezones(instance, workspace, external_repo):
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
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        ticks = instance.get_ticks(eastern_origin.get_id())
        assert len(ticks) == 0

        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        ticks = instance.get_ticks(eastern_origin.get_id())
        assert len(ticks) == 0

    # Past midnight eastern time, the eastern timezone schedule will run, but not the central timezone
    freeze_datetime = freeze_datetime.add(minutes=1)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(eastern_origin.get_id())
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

        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            instance.get_runs()[0],
            expected_datetime,
            create_pendulum_time(2019, 2, 27, tz="US/Eastern"),
        )

    # Past midnight central time, the central timezone schedule will now run
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):

        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(eastern_origin.get_id())
        assert len(ticks) == 1

        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=28, tz="US/Central"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[0].run_id],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            instance.get_runs()[0],
            expected_datetime,
            create_pendulum_time(2019, 2, 27, tz="US/Central"),
        )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        ticks = instance.get_ticks(eastern_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


# Verify that a schedule that runs in US/Central late enough in the day that it executes on
# a different day in UTC still runs and creates its partition names based on the US/Central time
def test_different_days_in_different_timezones(instance, workspace, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 2, 27, 22, 59, 59, tz="US/Central"), "US/Pacific"
    )
    with pendulum.test(freeze_datetime):
        # Runs every day at 11PM (CST)
        external_schedule = external_repo.get_external_schedule("daily_late_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1

        expected_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=27, hour=23, tz="US/Central"), "UTC"
        )

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[0].run_id],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            instance.get_runs()[0],
            expected_datetime,
            create_pendulum_time(2019, 2, 26, tz="US/Central"),
        )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


def test_hourly_dst_spring_forward(instance, workspace, external_repo):
    # Verify that an hourly schedule still runs hourly during the spring DST transition
    # 1AM CST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 3, 10, 1, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("hourly_central_time_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(hours=2)

    # DST has now happened, 2 hours later it is 4AM CST
    # Should be 3 runs: 1AM CST, 3AM CST, 4AM CST
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
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
                partition_time=to_timezone(expected_datetimes_utc[i], "US/Central").subtract(
                    hours=1
                ),
                partition_fmt=DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3


def test_hourly_dst_fall_back(instance, workspace, external_repo):
    # Verify that an hourly schedule still runs hourly during the fall DST transition
    # 12:30 AM CST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 11, 3, 0, 30, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("hourly_central_time_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(hours=4)

    # DST has now happened, 4 hours later it is 3:30AM CST
    # Should be 4 runs: 1AM CDT, 1AM CST, 2AM CST, 3AM CST
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 4
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 4

        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 3, 9, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 8, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 7, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 6, 0, 0, tz="UTC"),
        ]

        expected_ct_times = [
            "2019-11-03T03:00:00-06:00",  # 3 AM CST
            "2019-11-03T02:00:00-06:00",  # 2 AM CST
            "2019-11-03T01:00:00-06:00",  # 1 AM CST
            "2019-11-03T01:00:00-05:00",  # 1 AM CDT
        ]

        for i in range(4):
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
                partition_time=to_timezone(expected_datetimes_utc[i], "US/Central").subtract(
                    hours=1
                ),
                partition_fmt=DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 4
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 4


def test_daily_dst_spring_forward(instance, workspace, external_repo):
    # Verify that a daily schedule still runs once per day during the spring DST transition
    # Night before DST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 3, 10, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(days=2)

    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3

        # UTC time changed by one hour after the transition, still running daily at the same
        # time in CT
        expected_datetimes_utc = [
            create_pendulum_time(2019, 3, 12, 5, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 3, 11, 5, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 3, 10, 6, 0, 0, tz="UTC"),
        ]

        expected_partition_times = [
            create_pendulum_time(2019, 3, 11, tz="US/Central"),
            create_pendulum_time(2019, 3, 10, tz="US/Central"),
            create_pendulum_time(2019, 3, 9, tz="US/Central"),
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
                partition_time=expected_partition_times[i],
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3


def test_daily_dst_fall_back(instance, workspace, external_repo):
    # Verify that a daily schedule still runs once per day during the fall DST transition
    # Night before DST
    freeze_datetime = to_timezone(
        create_pendulum_time(2019, 11, 3, 0, 0, 0, tz="US/Central"), "US/Pacific"
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("daily_central_time_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(days=2)

    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3

        # UTC time changed by one hour after the transition, still running daily at the same
        # time in CT
        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 5, 6, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 4, 6, 0, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 5, 0, 0, tz="UTC"),
        ]

        expected_partition_times = [
            create_pendulum_time(2019, 11, 4, tz="US/Central"),
            create_pendulum_time(2019, 11, 3, tz="US/Central"),
            create_pendulum_time(2019, 11, 2, tz="US/Central"),
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
                partition_time=expected_partition_times[i],
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3


def test_execute_during_dst_transition_spring_forward(instance, workspace, external_repo):
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

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(days=3)

    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3

        expected_datetimes_utc = [
            to_timezone(create_pendulum_time(2019, 3, 11, 2, 30, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 10, 3, 00, 0, tz="US/Central"), "UTC"),
            to_timezone(create_pendulum_time(2019, 3, 9, 2, 30, 0, tz="US/Central"), "UTC"),
        ]

        expected_partition_times = [
            create_pendulum_time(2019, 3, 10, tz="US/Central"),
            create_pendulum_time(2019, 3, 9, tz="US/Central"),
            create_pendulum_time(2019, 3, 8, tz="US/Central"),
        ]

        partition_set_def = the_repo.get_partition_set_def(
            "daily_dst_transition_schedule_skipped_time_partitions"
        )
        partition_names = partition_set_def.get_partition_names()

        assert "2019-03-08" in partition_names
        assert "2019-03-09" in partition_names
        assert "2019-03-10" in partition_names

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
                partition_time=expected_partition_times[i],
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3


def test_execute_during_dst_transition_fall_back(instance, workspace, external_repo):
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

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(days=3)

    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3

        expected_datetimes_utc = [
            create_pendulum_time(2019, 11, 4, 7, 30, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 3, 7, 30, 0, tz="UTC"),
            create_pendulum_time(2019, 11, 2, 6, 30, 0, tz="UTC"),
        ]

        expected_partition_times = [
            create_pendulum_time(2019, 11, 3, tz="US/Central"),
            create_pendulum_time(2019, 11, 2, tz="US/Central"),
            create_pendulum_time(2019, 11, 1, tz="US/Central"),
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
                partition_time=expected_partition_times[i],
            )

        # Verify idempotence
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3
