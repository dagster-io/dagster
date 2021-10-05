from dagster.seven.compat.pendulum import create_pendulum_time
from dagster.utils.schedules import schedule_execution_time_iterator


def test_cron_schedule_advances_past_dst():
    # In Australia/Sydney, DST is at 2AM on 10/3/21. Verify that we don't
    # get stuck on the DST boundary.
    start_time = create_pendulum_time(
        year=2021, month=10, day=3, hour=1, minute=30, second=1, tz="Australia/Sydney"
    )

    time_iter = schedule_execution_time_iterator(
        start_time.timestamp(), "*/15 * * * *", "Australia/Sydney"
    )

    for _i in range(6):
        # 1:45, 3:00, 3:15, 3:30, 3:45, 4:00
        next_time = next(time_iter)

    assert (
        next_time.timestamp()
        == create_pendulum_time(
            year=2021, month=10, day=3, hour=4, tz="Australia/Sydney"
        ).timestamp()
    )
