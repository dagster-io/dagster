import pytest
from dagster._check import CheckError
from dagster._time import create_datetime
from dagster._utils.schedules import schedule_execution_time_iterator


def test_cron_schedule_advances_past_dst():
    # In Australia/Sydney, DST is at 2AM on 10/3/21. Verify that we don't
    # get stuck on the DST boundary.
    start_time = create_datetime(
        year=2021, month=10, day=3, hour=1, minute=30, second=1, tz="Australia/Sydney"
    )

    time_iter = schedule_execution_time_iterator(
        start_time.timestamp(), "*/15 * * * *", "Australia/Sydney"
    )

    for _i in range(6):
        # 1:45, 3:00, 3:15, 3:30, 3:45, 4:00
        next_time = next(time_iter)

    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2021, month=10, day=3, hour=4, tz="Australia/Sydney").timestamp()
    )


def test_vixie_cronstring_schedule():
    start_time = create_datetime(
        year=2022, month=2, day=21, hour=1, minute=30, second=1, tz="US/Pacific"
    )

    time_iter = schedule_execution_time_iterator(start_time.timestamp(), "@hourly", "US/Pacific")
    for _i in range(6):
        # 2:00, 3:00, 4:00, 5:00, 6:00, 7:00
        next_time = next(time_iter)
    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2022, month=2, day=21, hour=7, tz="US/Pacific").timestamp()
    )

    time_iter = schedule_execution_time_iterator(start_time.timestamp(), "@daily", "US/Pacific")
    for _i in range(6):
        # 2/22, 2/23, 2/24, 2/25, 2/26, 2/27
        next_time = next(time_iter)
    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2022, month=2, day=27, tz="US/Pacific").timestamp()
    )

    time_iter = schedule_execution_time_iterator(start_time.timestamp(), "@weekly", "US/Pacific")
    for _i in range(6):
        # 2/27, 3/6, 3/13, 3/20, 3/27, 4/3
        next_time = next(time_iter)
    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2022, month=4, day=3, tz="US/Pacific").timestamp()
    )

    time_iter = schedule_execution_time_iterator(start_time.timestamp(), "@monthly", "US/Pacific")
    for _i in range(6):
        # 3/1, 4/1, 5/1, 6/1, 7/1, 8/1
        next_time = next(time_iter)
    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2022, month=8, day=1, tz="US/Pacific").timestamp()
    )

    time_iter = schedule_execution_time_iterator(start_time.timestamp(), "@yearly", "US/Pacific")
    for _i in range(6):
        # 1/1/2023, 1/1/2024, 1/1/2025, 1/1/2026, 1/1/2027, 1/1/2028
        next_time = next(time_iter)
    assert (
        next_time.timestamp()  # pyright: ignore[reportPossiblyUnboundVariable]
        == create_datetime(year=2028, month=1, day=1, tz="US/Pacific").timestamp()
    )


def test_union_of_cron_strings_schedule():
    # Saturday
    start_time = create_datetime(year=2022, month=1, day=1, hour=2, tz="UTC")

    time_iter = schedule_execution_time_iterator(
        start_time.timestamp(),
        [
            "0 2 * * FRI-SAT",  # 02:00 Friday through Saturday
            "0 2,8 * * MON,FRI",  # 02:00, 08:00 on Monday and Friday
            "*/30 9 * * SUN",  # 09:00, 09:30 on Sunday
        ],
        "UTC",
    )
    # Test an entire week's cycle
    next_timestamps = [next(time_iter).timestamp() for _ in range(8)]

    expected_next_timestamps = [
        dt.timestamp()
        for dt in [
            create_datetime(year=2022, month=1, day=1, hour=2, tz="UTC"),
            create_datetime(year=2022, month=1, day=2, hour=9, tz="UTC"),
            create_datetime(year=2022, month=1, day=2, hour=9, minute=30, tz="UTC"),
            create_datetime(year=2022, month=1, day=3, hour=2, tz="UTC"),
            create_datetime(year=2022, month=1, day=3, hour=8, tz="UTC"),
            create_datetime(year=2022, month=1, day=7, hour=2, tz="UTC"),
            create_datetime(year=2022, month=1, day=7, hour=8, tz="UTC"),
            create_datetime(year=2022, month=1, day=8, hour=2, tz="UTC"),
        ]
    ]
    assert next_timestamps == expected_next_timestamps


def test_invalid_cron_string():
    start_time = create_datetime(
        year=2022, month=2, day=21, hour=1, minute=30, second=1, tz="US/Pacific"
    )

    with pytest.raises(CheckError):
        next(schedule_execution_time_iterator(start_time.timestamp(), "* * * * * *", "US/Pacific"))


def test_empty_cron_string_union():
    start_time = create_datetime(
        year=2022, month=2, day=21, hour=1, minute=30, second=1, tz="US/Pacific"
    )

    with pytest.raises(CheckError):
        next(schedule_execution_time_iterator(start_time.timestamp(), [], "US/Pacific"))


def test_first_monday():
    # start sunday 1/1/2023
    start_time = create_datetime(year=2023, month=1, day=1, tz="US/Pacific")
    iterator = schedule_execution_time_iterator(
        start_time.timestamp(), "0 0 * * mon#1", "US/Pacific"
    )
    # monday 1/2
    assert next(iterator) == create_datetime(year=2023, month=1, day=2, tz="US/Pacific")
    # monday 2/6
    assert next(iterator) == create_datetime(year=2023, month=2, day=6, tz="US/Pacific")
    # monday 3/6
    assert next(iterator) == create_datetime(year=2023, month=3, day=6, tz="US/Pacific")


def test_on_tick_boundary_simple():
    # Saturday
    start_time = create_datetime(year=2022, month=1, day=1, hour=2, tz="UTC")

    time_iter = schedule_execution_time_iterator(
        start_time.timestamp(),
        [
            "0 3 * * *",  # 03:00 every day
        ],
        "UTC",
    )
    # Test an entire week's cycle
    next_timestamps = [next(time_iter).timestamp() for _ in range(8)]

    expected_next_timestamps = [
        create_datetime(year=2022, month=1, day=i + 1, hour=3, tz="UTC").timestamp()
        for i in range(8)
    ]
    assert next_timestamps == expected_next_timestamps


def test_on_tick_boundary_complex():
    # Saturday
    start_time = create_datetime(year=2022, month=1, day=1, hour=2, tz="UTC")

    time_iter = schedule_execution_time_iterator(
        start_time.timestamp(),
        [
            "0 3 * * MON-FRI",  # 03:00 every day MON-FRI
        ],
        "UTC",
    )
    # Test an entire week's cycle
    next_timestamps = [next(time_iter).timestamp() for _ in range(10)]

    expected_next_timestamps = [
        create_datetime(year=2022, month=1, day=i + 1, hour=3, tz="UTC").timestamp()
        for i in (*range(2, 7), *range(9, 14))  # skip SAT and SUN
    ]
    assert next_timestamps == expected_next_timestamps
