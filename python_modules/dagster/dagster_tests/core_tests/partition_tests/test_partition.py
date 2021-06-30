from datetime import datetime, time
from typing import Callable, List, Optional

import pendulum
import pytest
from dagster.check import CheckError
from dagster.core.definitions.partition import (
    DynamicPartitionsDefinition,
    Partition,
    ScheduleTimeBasedPartitionsDefinition,
    ScheduleType,
    StaticPartitionsDefinition,
)
from dagster.seven.compat.pendulum import create_pendulum_time
from dagster.utils.partitions import DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE


def assert_expected_partitions(
    generated_partitions: List[Partition], expected_partitions: List[str]
):
    assert all(
        isinstance(generated_partition, Partition) for generated_partition in generated_partitions
    )
    assert len(generated_partitions) == len(expected_partitions)
    for generated_partition, expected_partition_name in zip(
        generated_partitions, expected_partitions
    ):
        assert generated_partition.name == expected_partition_name


@pytest.mark.parametrize(
    argnames=["partitions"],
    argvalues=[([Partition("a_partition")],), ([Partition(x) for x in range(10)],)],
)
def test_static_partitions(partitions: List[Partition]):
    static_partitions = StaticPartitionsDefinition(partitions)

    assert [(p.name, p.value) for p in static_partitions.get_partitions()] == [
        (p.name, p.value) for p in partitions
    ]


@pytest.mark.parametrize(
    argnames=["schedule_type", "start", "execution_day", "end", "error_message_regex"],
    ids=[
        "start should be before end",
        "hourly partitions, execution day should not be provided",
        "daily partitions, execution day should not be provided",
        "weekly partitions, execution day should be between 0 and 6",
        "monthly partitions, execution day should be between 1 and 31",
    ],
    argvalues=[
        (
            ScheduleType.DAILY,
            datetime(year=2021, month=1, day=3),
            None,
            datetime(year=2021, month=1, day=1),
            r"Selected date range start .* is after date range end",
        ),
        (
            ScheduleType.HOURLY,
            datetime(year=2021, month=1, day=1),
            1,
            datetime(year=2021, month=1, day=3),
            "Execution day should not be provided",
        ),
        (
            ScheduleType.DAILY,
            datetime(year=2021, month=1, day=1),
            1,
            datetime(year=2021, month=1, day=3),
            "Execution day should not be provided",
        ),
        (
            ScheduleType.WEEKLY,
            datetime(year=2021, month=1, day=1),
            7,
            datetime(year=2021, month=2, day=1),
            "Execution day .* must be between 0 and 6",
        ),
        (
            ScheduleType.MONTHLY,
            datetime(year=2021, month=1, day=1),
            0,
            datetime(year=2021, month=2, day=1),
            "Execution day .* must be between 1 and 31",
        ),
    ],
)
def test_time_based_partitions_invariants(
    schedule_type: ScheduleType,
    start: datetime,
    execution_day: Optional[int],
    end: Optional[datetime],
    error_message_regex: str,
):
    with pytest.raises(CheckError, match=error_message_regex):
        ScheduleTimeBasedPartitionsDefinition(
            schedule_type=schedule_type,
            start=start,
            execution_day=execution_day,
            execution_time=None,
            end=end,
            fmt=None,
            timezone=None,
            offset=None,
        )


@pytest.mark.parametrize(
    argnames=[
        "start",
        "execution_time",
        "end",
        "partition_days_offset",
        "current_time",
        "expected_partitions",
    ],
    ids=[
        "partition days offset == 0",
        "partition days offset == 1",
        "partition days offset > 1",
        "partition days offset > 1, current time before end partition time",
        "partition days offset > 1, current time after end partition time",
        "partition days offset > 1, current time shows all partitions",
        "partition days offset > 1, no partitions after end partition time",
        "partition days offset > 1, no end partition time",
        "different start/end year",
        "leap year",
        "not leap year",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            0,
            create_pendulum_time(2021, 1, 6, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05", "2021-01-06"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            1,
            create_pendulum_time(2021, 1, 6, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            2,
            create_pendulum_time(2021, 1, 6, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            2,
            create_pendulum_time(2021, 1, 5, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            2,
            create_pendulum_time(2021, 1, 7, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            2,
            create_pendulum_time(2021, 1, 8, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05", "2021-01-06"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            datetime(year=2021, month=1, day=6),
            2,
            create_pendulum_time(2022, 1, 8, 1, 20),
            ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04", "2021-01-05", "2021-01-06"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            time(1, 20),
            None,
            2,
            create_pendulum_time(2021, 1, 9, 1, 20),
            [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
                "2021-01-05",
                "2021-01-06",
                "2021-01-07",
            ],
        ),
        (
            datetime(year=2020, month=12, day=29),
            time(1, 20),
            datetime(year=2021, month=1, day=3),
            0,
            create_pendulum_time(2021, 1, 3, 1, 20),
            ["2020-12-29", "2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02", "2021-01-03"],
        ),
        (
            datetime(year=2020, month=2, day=28),
            time(1, 20),
            datetime(year=2020, month=3, day=3),
            0,
            create_pendulum_time(2020, 3, 3, 1, 20),
            ["2020-02-28", "2020-02-29", "2020-03-01", "2020-03-02", "2020-03-03"],
        ),
        (
            datetime(year=2021, month=2, day=28),
            time(1, 20),
            datetime(year=2021, month=3, day=3),
            0,
            create_pendulum_time(2021, 3, 3, 1, 20),
            ["2021-02-28", "2021-03-01", "2021-03-02", "2021-03-03"],
        ),
    ],
)
def test_time_partitions_daily_partitions(
    start: datetime,
    execution_time: time,
    end: datetime,
    partition_days_offset: Optional[int],
    current_time,
    expected_partitions: List[str],
):
    with pendulum.test(current_time):
        partitions = ScheduleTimeBasedPartitionsDefinition(
            schedule_type=ScheduleType.DAILY,
            start=start,
            execution_time=execution_time,
            end=end,
            offset=partition_days_offset,
        )

        assert_expected_partitions(partitions.get_partitions(), expected_partitions)


@pytest.mark.parametrize(
    argnames=[
        "start",
        "end",
        "partition_months_offset",
        "current_time",
        "expected_partitions",
    ],
    ids=[
        "partition months offset == 0",
        "partition months offset == 1",
        "partition months offset > 1",
        "partition months offset > 1, current time before end partition time",
        "partition months offset > 1, current time after end partition time",
        "partition months offset > 1, current time shows all partitions",
        "partition months offset > 1, no partitions after end partition time",
        "partition months offset > 1, no end partition time",
        "execution day of month not within start/end range",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            0,
            create_pendulum_time(2021, 3, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            1,
            create_pendulum_time(2021, 3, 1, 1, 20),
            ["2021-01-01", "2021-02-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            2,
            create_pendulum_time(2021, 3, 1, 1, 20),
            ["2021-01-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            2,
            create_pendulum_time(2021, 2, 27),
            [],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            2,
            create_pendulum_time(2021, 4, 1, 1, 20),
            ["2021-01-01", "2021-02-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            2,
            create_pendulum_time(2021, 5, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=3, day=1),
            2,
            create_pendulum_time(2021, 6, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            None,
            2,
            create_pendulum_time(2021, 6, 1, 1, 20),
            ["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01"],
        ),
        (
            datetime(year=2021, month=1, day=3),
            datetime(year=2021, month=1, day=31),
            0,
            create_pendulum_time(2021, 1, 31),
            [],
        ),
    ],
)
def test_time_partitions_monthly_partitions(
    start: datetime,
    end: datetime,
    partition_months_offset: Optional[int],
    current_time,
    expected_partitions: List[str],
):
    with pendulum.test(current_time):
        partitions = ScheduleTimeBasedPartitionsDefinition(
            schedule_type=ScheduleType.MONTHLY,
            start=start,
            execution_time=time(1, 20),
            execution_day=1,
            end=end,
            offset=partition_months_offset,
        )

        assert_expected_partitions(partitions.get_partitions(), expected_partitions)


@pytest.mark.parametrize(
    argnames=[
        "start",
        "end",
        "partition_weeks_offset",
        "current_time",
        "expected_partitions",
    ],
    ids=[
        "partition weeks offset == 0",
        "partition weeks offset == 1",
        "partition weeks offset > 1",
        "partition weeks offset > 1, current time before end partition time",
        "partition weeks offset > 1, current time after end partition time",
        "partition weeks offset > 1, current time shows all partitions",
        "partition weeks offset > 1, no partitions after end partition time",
        "partition weeks offset > 1, no end partition time",
        "execution day of week not within start/end range",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            0,
            create_pendulum_time(2021, 1, 31, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22", "2021-01-29"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            1,
            create_pendulum_time(2021, 1, 31, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            2,
            create_pendulum_time(2021, 1, 31, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            2,
            create_pendulum_time(2021, 1, 24, 1, 20),
            ["2021-01-01", "2021-01-08"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            2,
            create_pendulum_time(2021, 2, 7, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            2,
            create_pendulum_time(2021, 2, 14, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22", "2021-01-29"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            datetime(year=2021, month=1, day=31),
            2,
            create_pendulum_time(2021, 2, 21, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22", "2021-01-29"],
        ),
        (
            datetime(year=2021, month=1, day=1),
            None,
            2,
            create_pendulum_time(2021, 2, 21, 1, 20),
            ["2021-01-01", "2021-01-08", "2021-01-15", "2021-01-22", "2021-01-29", "2021-02-05"],
        ),
        (
            datetime(year=2021, month=1, day=4),
            datetime(year=2021, month=1, day=9),
            0,
            create_pendulum_time(2021, 1, 9),
            [],
        ),
    ],
)
def test_time_partitions_weekly_partitions(
    start: datetime,
    end: datetime,
    partition_weeks_offset: Optional[int],
    current_time,
    expected_partitions: List[str],
):
    with pendulum.test(current_time):
        partitions = ScheduleTimeBasedPartitionsDefinition(
            schedule_type=ScheduleType.WEEKLY,
            start=start,
            execution_time=time(1, 20),
            execution_day=0,
            end=end,
            offset=partition_weeks_offset,
        )

        assert_expected_partitions(partitions.get_partitions(), expected_partitions)


@pytest.mark.parametrize(
    argnames=[
        "start",
        "end",
        "timezone",
        "partition_hours_offset",
        "current_time",
        "expected_partitions",
    ],
    ids=[
        "partition hours offset == 0",
        "partition hours offset == 1",
        "partition hours offset > 1",
        "partition hours offset > 1, current time before end partition time",
        "partition hours offset > 1, current time after end partition time",
        "partition hours offset > 1, current time shows all partitions",
        "partition hours offset > 1, no partitions after end partition time",
        "partition hours offset > 1, no end partition time",
        "execution hour not within start/end range",
        "Spring DST",
        "Spring DST with timezone",
        "Fall DST",
        "Fall DST with timezone",
    ],
    argvalues=[
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            0,
            create_pendulum_time(2021, 1, 1, 4, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
                "2021-01-01-04:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            1,
            create_pendulum_time(2021, 1, 1, 4, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            2,
            create_pendulum_time(2021, 1, 1, 4, 1),
            ["2021-01-01-00:00+0000", "2021-01-01-01:00+0000", "2021-01-01-02:00+0000"],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            2,
            create_pendulum_time(2021, 1, 1, 3, 30),
            ["2021-01-01-00:00+0000", "2021-01-01-01:00+0000"],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            2,
            create_pendulum_time(2021, 1, 1, 5, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            2,
            create_pendulum_time(2021, 1, 1, 6, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
                "2021-01-01-04:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            datetime(year=2021, month=1, day=1, hour=4),
            None,
            2,
            create_pendulum_time(2021, 1, 1, 7, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
                "2021-01-01-04:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0),
            None,
            None,
            2,
            create_pendulum_time(2021, 1, 1, 7, 1),
            [
                "2021-01-01-00:00+0000",
                "2021-01-01-01:00+0000",
                "2021-01-01-02:00+0000",
                "2021-01-01-03:00+0000",
                "2021-01-01-04:00+0000",
                "2021-01-01-05:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=1, day=1, hour=0, minute=2),
            datetime(year=2021, month=1, day=1, hour=0, minute=59),
            None,
            0,
            create_pendulum_time(2021, 1, 1, 0, 59),
            [],
        ),
        (
            datetime(year=2021, month=3, day=14, hour=1),
            datetime(year=2021, month=3, day=14, hour=4),
            None,
            0,
            create_pendulum_time(2021, 3, 14, 4, 1),
            [
                "2021-03-14-01:00+0000",
                "2021-03-14-02:00+0000",
                "2021-03-14-03:00+0000",
                "2021-03-14-04:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=3, day=14, hour=1),
            datetime(year=2021, month=3, day=14, hour=4),
            "US/Central",
            0,
            create_pendulum_time(2021, 3, 14, 4, 1, tz="US/Central"),
            ["2021-03-14-01:00-0600", "2021-03-14-03:00-0500", "2021-03-14-04:00-0500"],
        ),
        (
            datetime(year=2021, month=11, day=7, hour=0),
            datetime(year=2021, month=11, day=7, hour=4),
            None,
            0,
            create_pendulum_time(2021, 11, 7, 4, 1),
            [
                "2021-11-07-00:00+0000",
                "2021-11-07-01:00+0000",
                "2021-11-07-02:00+0000",
                "2021-11-07-03:00+0000",
                "2021-11-07-04:00+0000",
            ],
        ),
        (
            datetime(year=2021, month=11, day=7, hour=0),
            datetime(year=2021, month=11, day=7, hour=4),
            "US/Central",
            0,
            create_pendulum_time(2021, 11, 7, 4, 1, tz="US/Central"),
            [
                "2021-11-07-00:00-0500",
                "2021-11-07-01:00-0500",
                "2021-11-07-01:00-0600",
                "2021-11-07-02:00-0600",
                "2021-11-07-03:00-0600",
                "2021-11-07-04:00-0600",
            ],
        ),
    ],
)
def test_time_partitions_hourly_partitions(
    start: datetime,
    end: datetime,
    timezone: Optional[str],
    partition_hours_offset: int,
    current_time,
    expected_partitions: List[str],
):
    with pendulum.test(current_time):
        partitions = ScheduleTimeBasedPartitionsDefinition(
            schedule_type=ScheduleType.HOURLY,
            start=start,
            execution_time=time(0, 1),
            end=end,
            timezone=timezone,
            fmt=DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            offset=partition_hours_offset,
        )

        assert_expected_partitions(partitions.get_partitions(), expected_partitions)


@pytest.mark.parametrize(
    argnames=["partition_fn"],
    argvalues=[
        (lambda _current_time: [Partition("a_partition")],),
        (lambda _current_time: [Partition(x) for x in range(10)],),
    ],
)
def test_dynamic_partitions(partition_fn: Callable[[Optional[datetime]], List[Partition]]):
    partitions = DynamicPartitionsDefinition(partition_fn)

    assert [(p.name, p.value) for p in partitions.get_partitions()] == [
        (p.name, p.value) for p in partition_fn(None)
    ]
