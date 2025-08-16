import calendar
import datetime

import pytest

from dagster._time import create_datetime, get_timezone
from dagster._utils.schedules import (
    _croniter_string_iterator,
    cron_string_iterator,
    get_smallest_cron_interval,
    is_valid_cron_string,
    reverse_cron_string_iterator,
)
from dagster_shared.check import CheckError


def test_cron_iterator_always_advances():
    tz = "Europe/Berlin"

    start_timestamp = create_datetime(2023, 3, 26, 2, 0, 0, tz=tz).timestamp() + 1

    expected_next_timestamp = 1679875200  # 2023-03-272:00+2:00

    # Verify that for all start timestamps until the next tick, cron_string_iterator behaves
    # as expected
    while start_timestamp < expected_next_timestamp:
        cron_iter = cron_string_iterator(
            start_timestamp + 1,
            "0 2 * * *",
            tz,
        )

        next_datetime = next(cron_iter)

        assert next_datetime.timestamp() > start_timestamp

        start_timestamp = start_timestamp + 75


def test_cron_iterator_leap_day():
    tz = "Europe/Berlin"

    start_timestamp = create_datetime(2023, 3, 27, 1, 0, 0, tz=tz).timestamp()

    cron_iter = cron_string_iterator(
        start_timestamp + 1,
        "2 4 29 2 *",
        tz,
    )

    for _ in range(100):
        next_datetime = next(cron_iter)
        assert next_datetime.day == 29
        assert calendar.isleap(next_datetime.year)
        assert next_datetime.hour == 4
        assert next_datetime.minute == 2


# Fall back: In Europe/Berlin on Sunday 10/29, 2AM-3AM happen twice (first with fold=0 / +2 offset,
# then fold=1, +1 offset)
# Spring forward: In Europe/Berlin on Sunday 3/26, 2AM jumps ahead to 3AM
# https://www.timeanddate.com/time/change/germany/berlin?year=2023
DST_PARAMS = [
    # Daily / fall back
    (
        "Europe/Berlin",
        "45 1 * * *",
        [
            create_datetime(2023, 10, 27, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 28, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 30, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 31, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 1, 1, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Australia/Lord_Howe",
        "0 2 * * *",
        [
            create_datetime(2023, 9, 29, 2, 0, 0, tz="Australia/Lord_Howe"),
            create_datetime(2023, 9, 30, 2, 0, 0, tz="Australia/Lord_Howe"),
            create_datetime(2023, 10, 1, 2, 30, 0, tz="Australia/Lord_Howe"),
            create_datetime(2023, 10, 2, 2, 0, 0, tz="Australia/Lord_Howe"),
            create_datetime(2023, 10, 3, 2, 0, 0, tz="Australia/Lord_Howe"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * *",
        [
            create_datetime(2023, 10, 27, 2, 0, 0, tz="Europe/Berlin"),  # +2:00
            create_datetime(2023, 10, 28, 2, 0, 0, tz="Europe/Berlin"),  # +2:00
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=1),  # +1:00
            create_datetime(2023, 10, 30, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
            create_datetime(2023, 10, 31, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
            create_datetime(2023, 11, 1, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * *",
        [
            create_datetime(2023, 10, 27, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 28, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 30, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 31, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 1, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_datetime(2023, 10, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 30, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 31, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 1, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Hourly / fall back
    (
        "Europe/Berlin",
        "45 * * * *",
        [
            create_datetime(2023, 10, 29, 0, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 3, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 * * * *",
        [
            create_datetime(2023, 10, 29, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Weekly / fall back
    (
        "Europe/Berlin",
        "45 1 * * 0",  # Every sunday at 1:45 AM
        [
            create_datetime(2023, 10, 15, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 22, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 5, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 12, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 19, 1, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * 0",  # Every sunday at 2 AM
        [
            create_datetime(2023, 10, 15, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 22, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 11, 5, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 12, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 19, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * 0",  # Every sunday at 2:30 AM
        [
            create_datetime(2023, 10, 15, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 22, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 11, 5, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 12, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 19, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * 0",  # Every sunday at 3:00 AM
        [
            create_datetime(2023, 10, 15, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 22, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 5, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 12, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 11, 19, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Monthly / fall back (11/5 2AM is turned back to 1AM)
    (
        "US/Central",
        "45 0 5 * *",  # 5th of each month at 00:45 (No DST issues)
        [
            create_datetime(2023, 9, 5, 0, 45, 0, tz="US/Central"),
            create_datetime(2023, 10, 5, 0, 45, 0, tz="US/Central"),
            create_datetime(2023, 11, 5, 0, 45, 0, tz="US/Central"),
            create_datetime(2023, 12, 5, 0, 45, 0, tz="US/Central"),
            create_datetime(2024, 1, 5, 0, 45, 0, tz="US/Central"),
        ],
    ),
    (
        "US/Central",
        "0 1 5 * *",  # 5th of each month at 1AM
        [
            create_datetime(2023, 9, 5, 1, 0, 0, tz="US/Central"),
            create_datetime(2023, 10, 5, 1, 0, 0, tz="US/Central"),
            create_datetime(2023, 11, 5, 1, 0, 0, tz="US/Central", fold=1),
            create_datetime(2023, 12, 5, 1, 0, 0, tz="US/Central"),
            create_datetime(2024, 1, 5, 1, 0, 0, tz="US/Central"),
        ],
    ),
    (
        "US/Central",
        "30 1 5 * *",  # 5th of each month at 130AM
        [
            create_datetime(2023, 9, 5, 1, 30, 0, tz="US/Central"),
            create_datetime(2023, 10, 5, 1, 30, 0, tz="US/Central"),
            create_datetime(2023, 11, 5, 1, 30, 0, tz="US/Central", fold=1),
            create_datetime(2023, 12, 5, 1, 30, 0, tz="US/Central"),
            create_datetime(2024, 1, 5, 1, 30, 0, tz="US/Central"),
        ],
    ),
    (
        "US/Central",
        "0 2 5 * *",  # 5th of each month at 2AM
        [
            create_datetime(2023, 9, 5, 2, 0, 0, tz="US/Central"),
            create_datetime(2023, 10, 5, 2, 0, 0, tz="US/Central"),
            create_datetime(2023, 11, 5, 2, 0, 0, tz="US/Central", fold=1),
            create_datetime(2023, 12, 5, 2, 0, 0, tz="US/Central"),
            create_datetime(2024, 1, 5, 2, 0, 0, tz="US/Central"),
        ],
    ),
    # Daily / spring forward
    (
        "Europe/Berlin",
        "0 1 * * *",
        [
            create_datetime(2023, 3, 24, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 25, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 27, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 28, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 29, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * *",
        [
            create_datetime(2023, 3, 24, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 25, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(  # 2AM on 3/26 does not exist, move forward
                2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
            ),
            create_datetime(2023, 3, 27, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 28, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 29, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * *",
        [
            create_datetime(2023, 3, 24, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 25, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(  # 2AM on 3/26 does not exist, move forward to 3AM
                2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
            ),
            create_datetime(2023, 3, 27, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 28, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 29, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_datetime(2023, 3, 24, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 25, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Weekly / spring forward
    (
        "Europe/Berlin",
        "0 1 * * 0",
        [
            create_datetime(2023, 3, 12, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 19, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 2, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 9, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 16, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * 0",
        [
            create_datetime(2023, 3, 12, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 19, 2, 0, 0, tz="Europe/Berlin"),
            # 2AM on 3/26 does not exist, move forward
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 2, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 9, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 16, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * 0",
        [
            create_datetime(2023, 3, 12, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 19, 2, 30, 0, tz="Europe/Berlin"),
            # 2:30AM on 3/26 does not exist, move forward
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 2, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 9, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 16, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * 0",
        [
            create_datetime(2023, 3, 12, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 19, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 2, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 9, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 16, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_datetime(2023, 3, 24, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 25, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Monthly / spring forward
    (
        "Europe/Berlin",
        "0 1 26 * *",
        [
            create_datetime(2023, 1, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 2, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 5, 26, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 26 * *",
        [
            create_datetime(2023, 1, 26, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 2, 26, 2, 0, 0, tz="Europe/Berlin"),
            # 2AM on 3/26 does not exist, move forward to 3AM
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 26, 2, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 5, 26, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 26 * *",
        [
            create_datetime(2023, 1, 26, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 2, 26, 2, 30, 0, tz="Europe/Berlin"),
            # 230AM on 3/26 does not exist, move forward to 3AM
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 26, 2, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 5, 26, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 26 * *",
        [
            create_datetime(2023, 1, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 2, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 4, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 5, 26, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Hourly / spring forward
    (
        "Europe/Berlin",
        "45 * * * *",
        [
            create_datetime(2023, 3, 26, 0, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 4, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 * * * *",
        [
            create_datetime(2023, 3, 26, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 4, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "*/15 * * * *",
        [
            create_datetime(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 15, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 1, 45, 0, tz="Europe/Berlin"),
            # 2 AM does not exist
            create_datetime(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 15, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 3, 26, 3, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "*/15 * * * *",
        [
            create_datetime(2023, 10, 29, 1, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 15, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 15, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", fold=0),
            create_datetime(2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 2, 15, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", fold=1),
            create_datetime(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 3, 15, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 3, 30, 0, tz="Europe/Berlin"),
            create_datetime(2023, 10, 29, 3, 45, 0, tz="Europe/Berlin"),
        ],
    ),
]


@pytest.mark.parametrize("execution_timezone,cron_string,times", DST_PARAMS)
@pytest.mark.parametrize(
    "force_croniter",
    [False, True],
)
def test_dst_transition_advances(execution_timezone, cron_string, times, force_croniter):
    # Starting 1 second after each time produces the next tick

    for i in range(len(times) - 1):
        orig_start_timestamp = times[i].astimezone(datetime.timezone.utc).timestamp()
        # first start from the timestamp that's exactly on the interval -
        # verify that it first returns the passed in timestamp, then advances

        if force_croniter:
            # Ensure that the croniter fallback would always produces the same results, even if we
            # don't end up using it
            fresh_cron_iter = _croniter_string_iterator(
                orig_start_timestamp, cron_string, execution_timezone
            )
        else:
            fresh_cron_iter = cron_string_iterator(
                orig_start_timestamp, cron_string, execution_timezone
            )
        prev_time = None
        for j in range(i, len(times)):
            next_time = next(fresh_cron_iter)

            orig_timestamp_str = datetime.datetime.fromtimestamp(
                orig_start_timestamp, tz=get_timezone(execution_timezone)
            )
            diff_str = next_time.timestamp() - times[j].timestamp()
            assert next_time.timestamp() == times[j].timestamp(), (
                f"Expected ({orig_timestamp_str}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {diff_str})"
            )
            prev_time = next_time

        start_timestamp = orig_start_timestamp + 1

        next_timestamp = times[i + 1].timestamp()

        # Spot-check 100 points on the interval between the two timestamps, making sure the last
        # one is very close to the end
        timestamp_interval = ((next_timestamp - 75) - orig_start_timestamp) / 100

        while start_timestamp < next_timestamp:
            if force_croniter:
                # Ensure that the croniter fallback would always produces the same results, even if we
                # don't end up using it
                fresh_cron_iter = _croniter_string_iterator(
                    start_timestamp, cron_string, execution_timezone
                )
            else:
                fresh_cron_iter = cron_string_iterator(
                    start_timestamp, cron_string, execution_timezone
                )

            prev_time = None
            for j in range(i + 1, len(times)):
                next_time = next(fresh_cron_iter)

                orig_timestamp_str = datetime.datetime.fromtimestamp(
                    orig_start_timestamp, tz=get_timezone(execution_timezone)
                )
                diff_str = next_time.timestamp() - times[j].timestamp()
                assert next_time.timestamp() == times[j].timestamp(), (
                    f"Expected ({orig_timestamp_str}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {diff_str})"
                )

                prev_time = next_time

            start_timestamp = start_timestamp + timestamp_interval


@pytest.mark.parametrize("execution_timezone,cron_string,times", DST_PARAMS)
@pytest.mark.parametrize(
    "force_croniter",
    [True, False],
)
def test_reversed_dst_transition_advances(execution_timezone, cron_string, times, force_croniter):
    times = list(reversed(times))
    for i in range(len(times) - 1):
        orig_start_timestamp = times[i].astimezone(datetime.timezone.utc).timestamp()

        # first start from the timestamp that's exactly on the interval -
        # verify that it first returns the passed in timestamp, then advances

        if force_croniter:
            # Ensure that the croniter fallback would always produces the same results, even if we
            # don't end up using it
            fresh_cron_iter = _croniter_string_iterator(
                orig_start_timestamp, cron_string, execution_timezone, ascending=False
            )
        else:
            fresh_cron_iter = reverse_cron_string_iterator(
                orig_start_timestamp, cron_string, execution_timezone
            )
        for j in range(i, len(times)):
            next_time = next(fresh_cron_iter)

            assert next_time.timestamp() == times[j].timestamp()

        start_timestamp = orig_start_timestamp - 1

        next_timestamp = times[i + 1].timestamp()

        # Spot-check 100 points on the interval between the two timestamps, making sure the last
        # one is very close to the end
        timestamp_interval = (orig_start_timestamp - (next_timestamp + 75)) / 100

        while start_timestamp > next_timestamp:
            if force_croniter:
                # Ensure that the croniter fallback would always produces the same results, even if we
                # don't end up using it
                fresh_cron_iter = _croniter_string_iterator(
                    start_timestamp, cron_string, execution_timezone, ascending=False
                )
            else:
                fresh_cron_iter = reverse_cron_string_iterator(
                    start_timestamp, cron_string, execution_timezone
                )

            prev_time = None
            for j in range(i + 1, len(times)):
                next_time = next(fresh_cron_iter)

                orig_timestamp_str = datetime.datetime.fromtimestamp(
                    orig_start_timestamp, tz=get_timezone(execution_timezone)
                )
                diff_str = next_time.timestamp() - times[j].timestamp()
                assert next_time.timestamp() == times[j].timestamp(), (
                    f"Expected ({orig_timestamp_str}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {diff_str})"
                )

                prev_time = next_time

            start_timestamp = start_timestamp - timestamp_interval


def test_last_day_of_month_cron_schedule():
    # L means last day of month
    execution_timezone = "Europe/Berlin"
    cron_string = "*/15 13 L * *"

    expected_datetimes = [
        create_datetime(2023, 10, 31, 13, 0, 0, tz="Europe/Berlin"),
        create_datetime(2023, 10, 31, 13, 15, 0, tz="Europe/Berlin"),
        create_datetime(2023, 10, 31, 13, 30, 0, tz="Europe/Berlin"),
        create_datetime(2023, 10, 31, 13, 45, 0, tz="Europe/Berlin"),
        create_datetime(2023, 11, 30, 13, 0, 0, tz="Europe/Berlin"),
        create_datetime(2023, 11, 30, 13, 15, 0, tz="Europe/Berlin"),
        create_datetime(2023, 11, 30, 13, 30, 0, tz="Europe/Berlin"),
        create_datetime(2023, 11, 30, 13, 45, 0, tz="Europe/Berlin"),
        create_datetime(2023, 12, 31, 13, 0, 0, tz="Europe/Berlin"),
        create_datetime(2023, 12, 31, 13, 15, 0, tz="Europe/Berlin"),
        create_datetime(2023, 12, 31, 13, 30, 0, tz="Europe/Berlin"),
        create_datetime(2023, 12, 31, 13, 45, 0, tz="Europe/Berlin"),
    ]

    start_timestamp = expected_datetimes[0].timestamp() - 1

    cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)

    for i in range(len(expected_datetimes)):
        assert next(cron_iter) == expected_datetimes[i]

    end_timestamp = expected_datetimes[-1].timestamp() + 1

    cron_iter = reverse_cron_string_iterator(end_timestamp, cron_string, execution_timezone)

    for i in range(len(expected_datetimes)):
        assert next(cron_iter) == expected_datetimes[-(i + 1)]


def test_weekend_cron_schedule_with_sunday_as_7():
    execution_timezone = "Europe/Berlin"
    cron_strings = ["0 0 * * 6-7", "0 0 * * 0,6"]
    for cron_string in cron_strings:
        expected_datetimes = [
            create_datetime(2024, 10, 26, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2024, 10, 27, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2024, 11, 2, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2024, 11, 3, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2024, 11, 9, 0, 0, 0, tz="Europe/Berlin"),
            create_datetime(2024, 11, 10, 0, 0, 0, tz="Europe/Berlin"),
        ]

        start_timestamp = expected_datetimes[0].timestamp() - 1

        cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)

        for i in range(len(expected_datetimes)):
            assert next(cron_iter) == expected_datetimes[i]

        end_timestamp = expected_datetimes[-1].timestamp() + 1

        cron_iter = reverse_cron_string_iterator(end_timestamp, cron_string, execution_timezone)

        for i in range(len(expected_datetimes)):
            assert next(cron_iter) == expected_datetimes[-(i + 1)]


def test_invalid_cron_strings():
    assert is_valid_cron_string("0 0 27 2 *")
    assert is_valid_cron_string("0 0 28 2 *")
    assert is_valid_cron_string("0 0 29 2 *")
    assert is_valid_cron_string("0 0 29 2 3")

    assert not is_valid_cron_string("0 0 30 2 *")
    assert not is_valid_cron_string("0 0 30 2 3")

    assert not is_valid_cron_string("0 0 31 2 *")
    assert not is_valid_cron_string("0 0 31 2 3")

    assert not is_valid_cron_string("0 0 32 2 *")

    assert is_valid_cron_string("0 0 31 1 *")
    assert not is_valid_cron_string("0 0 32 1 *")


def test_get_smallest_cron_interval_basic():
    """Test basic cron intervals return expected minimums."""
    # Minute intervals
    assert get_smallest_cron_interval("*/5 * * * *") == datetime.timedelta(minutes=5)
    assert get_smallest_cron_interval("*/15 * * * *") == datetime.timedelta(minutes=15)
    assert get_smallest_cron_interval("*/30 * * * *") == datetime.timedelta(minutes=30)

    # Hourly intervals
    assert get_smallest_cron_interval("0 * * * *") == datetime.timedelta(hours=1)
    assert get_smallest_cron_interval("0 */6 * * *") == datetime.timedelta(hours=6)
    assert get_smallest_cron_interval("0 */12 * * *") == datetime.timedelta(hours=12)

    # Daily intervals
    assert get_smallest_cron_interval("0 0 * * *") == datetime.timedelta(days=1)
    assert get_smallest_cron_interval("30 14 * * *") == datetime.timedelta(days=1)

    # Weekly intervals
    assert get_smallest_cron_interval("0 0 * * 0") == datetime.timedelta(days=7)
    assert get_smallest_cron_interval("0 9 * * 1") == datetime.timedelta(days=7)


def test_get_smallest_cron_interval_irregular():
    """Test irregular cron schedules return correct minimum intervals."""
    # Multiple times per hour
    interval = get_smallest_cron_interval("15,45 * * * *")
    assert interval == datetime.timedelta(minutes=30)

    # Multiple times per day
    interval = get_smallest_cron_interval("0 9,17 * * *")
    assert interval == datetime.timedelta(hours=8)

    # Weekdays only
    interval = get_smallest_cron_interval("0 9 * * 1-5")
    assert interval == datetime.timedelta(days=1)  # Daily on weekdays

    # Multiple days per week
    interval = get_smallest_cron_interval("0 9 * * 1,3,5")
    assert interval == datetime.timedelta(days=2)  # Mon->Wed->Fri pattern


def test_get_smallest_cron_interval_monthly():
    """Test monthly cron schedules."""
    # Monthly on 1st
    interval = get_smallest_cron_interval("0 0 1 * *")
    # Shortest month interval is 28 days (February)
    assert interval == datetime.timedelta(days=28)

    # Monthly on 15th
    interval = get_smallest_cron_interval("0 12 15 * *")
    assert interval == datetime.timedelta(days=28)


def test_get_smallest_cron_interval_leap_year():
    """Test leap year edge case with Feb 29th."""
    # Feb 29th only runs on leap years
    interval = get_smallest_cron_interval("0 0 29 2 *")
    # Should be 1 year for non-leap years, but our sampling should catch 4-year intervals
    # during leap year sequences
    assert interval.days >= 365  # At least 1 year

    # The exact value depends on when we sample, but should be reasonable
    assert interval.days <= 4 * 365 + 1  # At most 4 years + leap day


def test_get_smallest_cron_interval_dst_transitions():
    """Test DST transition edge cases."""
    # Daily at 2am in a DST timezone - should catch the 23-hour interval during spring forward
    interval = get_smallest_cron_interval("0 2 * * *", "America/New_York")
    assert interval == datetime.timedelta(hours=23)

    # Hourly schedule should not be affected by DST for minimum interval
    interval = get_smallest_cron_interval("0 * * * *", "America/New_York")
    assert interval == datetime.timedelta(hours=1)

    # Different timezone with DST
    interval = get_smallest_cron_interval("0 2 * * *", "Europe/Berlin")
    assert interval == datetime.timedelta(hours=23)


def test_get_smallest_cron_interval_timezones():
    """Test various timezones work correctly."""
    # UTC should work
    interval = get_smallest_cron_interval("*/10 * * * *", "UTC")
    assert interval == datetime.timedelta(minutes=10)

    # Other timezones should work
    interval = get_smallest_cron_interval("*/10 * * * *", "Asia/Tokyo")
    assert interval == datetime.timedelta(minutes=10)

    # Default timezone (UTC) should work
    interval = get_smallest_cron_interval("*/10 * * * *")
    assert interval == datetime.timedelta(minutes=10)


def test_get_smallest_cron_interval_complex_patterns():
    """Test complex cron patterns."""
    # Every 5 minutes during business hours on weekdays
    interval = get_smallest_cron_interval("*/5 9-17 * * 1-5")
    assert interval == datetime.timedelta(minutes=5)

    # Multiple specific times
    interval = get_smallest_cron_interval("0,30 8,12,16 * * 1-5")
    assert interval == datetime.timedelta(minutes=30)

    # Specific day patterns
    interval = get_smallest_cron_interval("0 9 1,15 * *")  # 1st and 15th of month
    # Minimum should be 14 days (15th to 1st of next month can be 14-17 days)
    assert interval.days >= 14
    assert interval.days <= 17


def test_get_smallest_cron_interval_edge_cases():
    """Test edge cases and error conditions."""
    # Invalid cron string should raise error
    with pytest.raises(CheckError):
        get_smallest_cron_interval("invalid cron")

    with pytest.raises(CheckError):
        get_smallest_cron_interval("0 0 32 * *")  # Invalid day

    # Valid but unusual patterns
    interval = get_smallest_cron_interval("0 0 * * *")  # Daily
    assert interval == datetime.timedelta(days=1)

    # Very frequent pattern
    interval = get_smallest_cron_interval("* * * * *")  # Every minute
    assert interval == datetime.timedelta(minutes=1)


def test_get_smallest_cron_interval_consistency():
    """Test that the method returns consistent results."""
    # Run the same cron string multiple times to ensure consistency
    cron_string = "*/15 * * * *"
    timezone = "America/Los_Angeles"

    results = []
    for _ in range(3):
        interval = get_smallest_cron_interval(cron_string, timezone)
        results.append(interval)

    # All results should be the same
    assert all(result == results[0] for result in results)
    assert results[0] == datetime.timedelta(minutes=15)
