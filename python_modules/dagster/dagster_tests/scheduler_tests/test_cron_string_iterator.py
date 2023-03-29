# ruff: noqa: T201

from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils.schedules import cron_string_iterator

time_sequences = (
    "Europe/Berlin",
    "0 2 * * *",
    [
        create_pendulum_time(2023, 3, 24, 2, 0, 0, tz="Europe/Berlin"),
        create_pendulum_time(2023, 3, 25, 2, 0, 0, tz="Europe/Berlin"),
        create_pendulum_time(  # 2AM on 3/26 does not exist, move forward
            2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
        ),
        create_pendulum_time(2023, 3, 27, 2, 0, 0, tz="Europe/Berlin"),  # return to 2AM
        create_pendulum_time(2023, 3, 28, 2, 0, 0, tz="Europe/Berlin"),
    ],
)


def test_dst_spring_forward_transition():
    execution_timezone, cron_string, times = time_sequences

    start_timestamp = to_timezone(times[0], "UTC").timestamp()

    cron_iter = cron_string_iterator(
        start_timestamp + 1,
        cron_string,
        execution_timezone,
    )

    # A single cron_iter covers the expected times
    for i in range(1, len(times)):
        next_datetime = next(cron_iter)
        print(f"Next time: {next_datetime} Expected: {times[i]}")
        assert next_datetime.timestamp() == times[i].timestamp()

    # Starting 1 second after each time individually also produces the next tick
    for i in range(len(times) - 1):
        start_timestamp = to_timezone(times[i], "UTC").timestamp() + 1
        fresh_cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)

        for j in range(i + 1, len(times) - 1):
            next_time = next(fresh_cron_iter)

            assert (
                next_time.timestamp() == times[j].timestamp()
            ), f"Expected {times[i]} to advance to {times[j]}, got {str(next_time)}"
