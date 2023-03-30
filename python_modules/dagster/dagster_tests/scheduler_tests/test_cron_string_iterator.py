from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils.schedules import cron_string_iterator


def test_cron_iterator_always_advances():
    tz = "Europe/Berlin"

    start_timestamp = create_pendulum_time(2023, 3, 27, 1, 0, 0, tz=tz).timestamp()

    cron_iter = cron_string_iterator(
        start_timestamp + 1,
        "0 2 * * *",
        tz,
    )

    next_datetime = next(cron_iter)

    assert next_datetime.timestamp() > start_timestamp


# These are not what one might expect due to upstream croniter bugs, but verifies that we
# don't get stuck
time_sequences = (
    "Europe/Berlin",
    "0 2 * * *",
    [
        create_pendulum_time(2023, 3, 24, 2, 0, 0, tz="Europe/Berlin"),
        create_pendulum_time(2023, 3, 25, 2, 0, 0, tz="Europe/Berlin"),
        create_pendulum_time(  # 2AM on 3/26 does not exist, move forward
            2023, 3, 26, 3, 0, 0, tz="Europe/Berlin"
        ),
        create_pendulum_time(
            2023, 3, 27, 1, 0, 0, tz="Europe/Berlin"
        ),  # Should be 2AM, is 1AM due to croniter bug
        create_pendulum_time(  # 3/28 fires twice due to croniter bug
            2023, 3, 28, 1, 0, 0, tz="Europe/Berlin"
        ),
        create_pendulum_time(2023, 3, 28, 2, 0, 0, tz="Europe/Berlin"),
        create_pendulum_time(2023, 3, 29, 2, 0, 0, tz="Europe/Berlin"),
    ],
)


def test_dst_spring_forward_transition_advances():
    execution_timezone, cron_string, times = time_sequences

    start_timestamp = to_timezone(times[0], "UTC").timestamp()

    cron_string_iterator(
        start_timestamp + 1,
        cron_string,
        execution_timezone,
    )

    # Starting 1 second after each time individually also produces the next tick
    for i in range(len(times) - 1):
        start_timestamp = to_timezone(times[i], "UTC").timestamp() + 1
        fresh_cron_iter = cron_string_iterator(start_timestamp, cron_string, execution_timezone)
        next_time = next(fresh_cron_iter)

        assert (
            next_time.timestamp() == times[i + 1].timestamp()
        ), f"Expected {times[i]} to advance to {times[i+1]}, got {str(next_time)}"
