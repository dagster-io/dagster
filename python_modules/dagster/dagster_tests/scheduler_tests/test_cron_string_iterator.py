import calendar

import pendulum
import pytest
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils.schedules import cron_string_iterator, reverse_cron_string_iterator


def test_cron_iterator_always_advances():
    tz = "Europe/Berlin"

    start_timestamp = create_pendulum_time(2023, 3, 26, 2, 0, 0, tz=tz).timestamp() + 1

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

    start_timestamp = create_pendulum_time(2023, 3, 27, 1, 0, 0, tz=tz).timestamp()

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


# Fall back: In Europe/Berlin on Sunday 10/29, 2AM-3AM happen twice (first with dst_rule=PRE_TRANSITION / +2 offset,
# then dst_rule=POST_TRANSITION, +1 offset)
# Spring forward: In Europe/Berlin on Sunday 3/26, 2AM jumps ahead to 3AM
# https://www.timeanddate.com/time/change/germany/berlin?year=2023
DST_PARAMS = [
    # Daily / fall back
    (
        "Europe/Berlin",
        "45 1 * * *",
        [
            create_pendulum_time(2023, 10, 27, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 28, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 30, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 31, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 1, 1, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * *",
        [
            create_pendulum_time(2023, 10, 27, 2, 0, 0, tz="Europe/Berlin"),  # +2:00
            create_pendulum_time(2023, 10, 28, 2, 0, 0, tz="Europe/Berlin"),  # +2:00
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),  # +1:00
            create_pendulum_time(2023, 10, 30, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
            create_pendulum_time(2023, 10, 31, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
            create_pendulum_time(2023, 11, 1, 2, 0, 0, tz="Europe/Berlin"),  # +1:00
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * *",
        [
            create_pendulum_time(
                2023, 10, 27, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 28, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 30, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 31, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 1, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_pendulum_time(2023, 10, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 30, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 31, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 1, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Hourly / fall back
    (
        "Europe/Berlin",
        "45 * * * *",
        [
            create_pendulum_time(2023, 10, 29, 0, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(
                2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(2023, 10, 29, 3, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 * * * *",
        [
            create_pendulum_time(2023, 10, 29, 0, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Weekly / fall back
    (
        "Europe/Berlin",
        "45 1 * * 0",  # Every sunday at 1:45 AM
        [
            create_pendulum_time(2023, 10, 15, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 22, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 5, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 12, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 19, 1, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * 0",  # Every sunday at 2 AM
        [
            create_pendulum_time(
                2023, 10, 15, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 22, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 5, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 12, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 19, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * 0",  # Every sunday at 2:30 AM
        [
            create_pendulum_time(
                2023, 10, 15, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 22, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 5, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 12, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 19, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * 0",  # Every sunday at 3:00 AM
        [
            create_pendulum_time(2023, 10, 15, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 22, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 5, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 12, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 11, 19, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Monthly / fall back (11/5 2AM is turned back to 1AM)
    (
        "US/Central",
        "45 0 5 * *",  # 5th of each month at 00:45 (No DST issues)
        [
            create_pendulum_time(2023, 9, 5, 0, 45, 0, tz="US/Central"),
            create_pendulum_time(2023, 10, 5, 0, 45, 0, tz="US/Central"),
            create_pendulum_time(2023, 11, 5, 0, 45, 0, tz="US/Central"),
            create_pendulum_time(2023, 12, 5, 0, 45, 0, tz="US/Central"),
            create_pendulum_time(2024, 1, 5, 0, 45, 0, tz="US/Central"),
        ],
    ),
    (
        "US/Central",
        "0 1 5 * *",  # 5th of each month at 1AM
        [
            create_pendulum_time(
                2023, 9, 5, 1, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 5, 1, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 5, 1, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 12, 5, 1, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2024, 1, 5, 1, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    (
        "US/Central",
        "30 1 5 * *",  # 5th of each month at 130AM
        [
            create_pendulum_time(
                2023, 9, 5, 1, 30, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 5, 1, 30, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 5, 1, 30, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 12, 5, 1, 30, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2024, 1, 5, 1, 30, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    (
        "US/Central",
        "0 2 5 * *",  # 5th of each month at 2AM
        [
            create_pendulum_time(
                2023, 9, 5, 2, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 5, 2, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 11, 5, 2, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 12, 5, 2, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2024, 1, 5, 2, 0, 0, tz="US/Central", dst_rule=pendulum.POST_TRANSITION
            ),
        ],
    ),
    # Daily / spring forward
    (
        "Europe/Berlin",
        "0 1 * * *",
        [
            create_pendulum_time(2023, 3, 24, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 25, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 27, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 28, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 29, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * *",
        [
            create_pendulum_time(2023, 3, 24, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 25, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(  # 2AM on 3/26 does not exist, move forward
                2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
            ),
            create_pendulum_time(2023, 3, 27, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 28, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 29, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * *",
        [
            create_pendulum_time(2023, 3, 24, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 25, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(  # 2AM on 3/26 does not exist, move forward to 3AM
                2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
            ),
            create_pendulum_time(2023, 3, 27, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 28, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 29, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_pendulum_time(2023, 3, 24, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 25, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Weekly / spring forward
    (
        "Europe/Berlin",
        "0 1 * * 0",
        [
            create_pendulum_time(2023, 3, 12, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 19, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 2, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 9, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 16, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 * * 0",
        [
            create_pendulum_time(2023, 3, 12, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 19, 2, 0, 0, tz="Europe/Berlin"),
            # 2AM on 3/26 does not exist, move forward
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 2, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 9, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 16, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 * * 0",
        [
            create_pendulum_time(2023, 3, 12, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 19, 2, 30, 0, tz="Europe/Berlin"),
            # 2:30AM on 3/26 does not exist, move forward
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 2, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 9, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 16, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * 0",
        [
            create_pendulum_time(2023, 3, 12, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 19, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 2, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 9, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 16, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 * * *",
        [
            create_pendulum_time(2023, 3, 24, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 25, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 27, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 28, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 29, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Monthly / spring forward
    (
        "Europe/Berlin",
        "0 1 26 * *",
        [
            create_pendulum_time(2023, 1, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 2, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 5, 26, 1, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 2 26 * *",
        [
            create_pendulum_time(2023, 1, 26, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 2, 26, 2, 0, 0, tz="Europe/Berlin"),
            # 2AM on 3/26 does not exist, move forward to 3AM
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 26, 2, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 5, 26, 2, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "30 2 26 * *",
        [
            create_pendulum_time(2023, 1, 26, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 2, 26, 2, 30, 0, tz="Europe/Berlin"),
            # 230AM on 3/26 does not exist, move forward to 3AM
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 26, 2, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 5, 26, 2, 30, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 3 26 * *",
        [
            create_pendulum_time(2023, 1, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 2, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 4, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 5, 26, 3, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    # Hourly / spring forward
    (
        "Europe/Berlin",
        "45 * * * *",
        [
            create_pendulum_time(2023, 3, 26, 0, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 4, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "0 * * * *",
        [
            create_pendulum_time(2023, 3, 26, 0, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 4, 0, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "*/15 * * * *",
        [
            create_pendulum_time(2023, 3, 26, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 15, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 1, 45, 0, tz="Europe/Berlin"),
            # 2 AM does not exist
            create_pendulum_time(2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 15, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 3, 26, 3, 45, 0, tz="Europe/Berlin"),
        ],
    ),
    (
        "Europe/Berlin",
        "*/15 * * * *",
        [
            create_pendulum_time(2023, 10, 29, 1, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 15, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 1, 45, 0, tz="Europe/Berlin"),
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 15, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", dst_rule=pendulum.PRE_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 15, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 30, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(
                2023, 10, 29, 2, 45, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
            ),
            create_pendulum_time(2023, 10, 29, 3, 0, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 3, 15, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 3, 30, 0, tz="Europe/Berlin"),
            create_pendulum_time(2023, 10, 29, 3, 45, 0, tz="Europe/Berlin"),
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
        orig_start_timestamp = to_timezone(times[i], "UTC").timestamp()
        # first start from the timestamp that's exactly on the interval -
        # verify that it first returns the passed in timestamp, then advances
        fresh_cron_iter = cron_string_iterator(
            orig_start_timestamp, cron_string, execution_timezone, force_croniter=force_croniter
        )
        prev_time = None
        for j in range(i, len(times)):
            next_time = next(fresh_cron_iter)

            assert (
                next_time.timestamp() == times[j].timestamp()
            ), f"Expected ({pendulum.from_timestamp(orig_start_timestamp, tz=execution_timezone)}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {next_time.timestamp() - times[j].timestamp()})"
            prev_time = next_time

        start_timestamp = orig_start_timestamp + 1

        next_timestamp = times[i + 1].timestamp()

        # Spot-check 100 points on the interval between the two timestamps, making sure the last
        # one is very close to the end
        timestamp_interval = ((next_timestamp - 75) - orig_start_timestamp) / 100

        while start_timestamp < next_timestamp:
            fresh_cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)

            prev_time = None
            for j in range(i + 1, len(times)):
                next_time = next(fresh_cron_iter)

                assert (
                    next_time.timestamp() == times[j].timestamp()
                ), f"Expected ({pendulum.from_timestamp(start_timestamp, tz=execution_timezone)}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {next_time.timestamp() - times[j].timestamp()})"

                prev_time = next_time

            start_timestamp = start_timestamp + timestamp_interval


@pytest.mark.parametrize("execution_timezone,cron_string,times", DST_PARAMS)
@pytest.mark.parametrize(
    "force_croniter",
    [False, True],
)
def test_reversed_dst_transition_advances(execution_timezone, cron_string, times, force_croniter):
    times = list(reversed(times))
    for i in range(len(times) - 1):
        orig_start_timestamp = to_timezone(times[i], "UTC").timestamp()

        # first start from the timestamp that's exactly on the interval -
        # verify that it first returns the passed in timestamp, then advances
        fresh_cron_iter = reverse_cron_string_iterator(
            orig_start_timestamp, cron_string, execution_timezone, force_croniter=force_croniter
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
            fresh_cron_iter = reverse_cron_string_iterator(
                start_timestamp, cron_string, execution_timezone
            )

            prev_time = None
            for j in range(i + 1, len(times)):
                next_time = next(fresh_cron_iter)

                assert (
                    next_time.timestamp() == times[j].timestamp()
                ), f"Expected ({pendulum.from_timestamp(start_timestamp, tz=execution_timezone)}) to advance from {prev_time} to {times[j]}, got {next_time} (Difference: {next_time.timestamp() - times[j].timestamp()})"

                prev_time = next_time

            start_timestamp = start_timestamp - timestamp_interval
