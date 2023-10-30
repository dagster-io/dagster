import calendar

import pendulum
import pytest
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils.schedules import cron_string_iterator


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


@pytest.mark.parametrize(
    "execution_timezone,cron_string,times",
    [
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
                create_pendulum_time(
                    2023, 10, 27, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
                create_pendulum_time(
                    2023, 10, 28, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
                create_pendulum_time(
                    2023, 10, 29, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
                create_pendulum_time(
                    2023, 10, 30, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
                create_pendulum_time(
                    2023, 10, 31, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
                create_pendulum_time(
                    2023, 11, 1, 2, 0, 0, tz="Europe/Berlin", dst_rule=pendulum.POST_TRANSITION
                ),
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
    ],
)
def test_dst_transition_advances(execution_timezone, cron_string, times):
    # Starting 1 second after each time produces the next tick
    for i in range(len(times) - 1):
        orig_start_timestamp = to_timezone(times[i], "UTC").timestamp() + 1
        start_timestamp = orig_start_timestamp

        next_timestamp = times[i + 1].timestamp()
        # Verify that for any start timestamp until the next tick, cron_string_iterator behaves
        # as expected
        while start_timestamp < next_timestamp:
            fresh_cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)

            for j in range(i + 1, len(times)):
                next_time = next(fresh_cron_iter)

                assert (
                    next_time.timestamp() == times[j].timestamp()
                ), f"Expected {times[i]} (starting from offset ({next_timestamp - start_timestamp}) to advance to {times[j]}, got {next_time} (Difference: {next_time.timestamp() - times[j].timestamp()})"

            start_timestamp = start_timestamp + 75
