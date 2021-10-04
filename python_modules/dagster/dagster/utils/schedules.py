import datetime
import pytz
from typing import Iterator, Optional

import pendulum
from croniter import croniter
from dagster import check
from dagster.seven.compat.pendulum import to_timezone


def schedule_execution_time_iterator(
    start_timestamp: float,
    schedule_type: ScheduleType,
    cron_schedule: str,
    execution_timezone: Optional[str],
) -> Iterator[datetime.datetime]:
    if schedule_type == ScheduleType.CRON_BASED:
        yield from _schedule_cron_iterator(start_timestamp, cron_schedule, execution_timezone)
    else:
        yield from _schedule_interval_iterator(
            start_timestamp, schedule_type, cron_schedule, execution_timezone
        )


def _schedule_interval_iterator(
    start_timestamp: float,
    schedule_type: ScheduleType,
    cron_schedule: str,
    execution_timezone: Optional[str],
) -> Iterator[datetime.datetime]:
    timezone_str = execution_timezone if execution_timezone else "UTC"

    start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

    # TODO Remove croniter dependency here
    date_iter = croniter(cron_schedule, start_datetime)

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    next_date = date_iter.get_prev(datetime.datetime)

    if schedule_type == ScheduleType.MONTHLY:  # monthly
        delta_fn = lambda d, num: d.add(months=num)
        should_hour_change = False
    elif schedule_type == ScheduleType.WEEKLY:  # weekly
        delta_fn = lambda d, num: d.add(weeks=num)
        should_hour_change = False
    elif schedule_type == ScheduleType.DAILY:  # daily
        delta_fn = lambda d, num: d.add(days=num)
        should_hour_change = False
    elif schedule_type == ScheduleType.HOURLY:  # hourly
        delta_fn = lambda d, num: d.add(hours=num)
        should_hour_change = True
    else:
        raise Exception(f"Unexpected schedule type {schedule_type}")

    while True:
        curr_hour = next_date.hour
        next_date_cand = delta_fn(next_date, 1)
        new_hour = next_date_cand.hour

        if not should_hour_change and new_hour != curr_hour:
            # If the hour changes during a daily/weekly/monthly schedule, it
            # indicates that the time shifted due to falling in a time that doesn't
            # exist due to a DST transition (for example, 2:30AM CST on 3/10/2019).
            # Instead, execute at the first time that does exist (the start of the hour),
            # but return to the original hour for all subsequent executions so that the
            # hour doesn't stay different permanently.

            check.invariant(new_hour == curr_hour + 1)
            yield next_date_cand.replace(minute=0)

            next_date_cand = delta_fn(next_date, 2)
            check.invariant(next_date_cand.hour == curr_hour)

        next_date = next_date_cand

        yield next_date


def _schedule_cron_iterator(
    start_timestamp: float, cron_schedule: str, execution_timezone: Optional[str]
) -> Iterator[datetime.datetime]:
    timezone_str = execution_timezone if execution_timezone else "UTC"

    print("ITERATING: " + str(start_timestamp) + " , " + str(execution_timezone))

    start_datetime = pytz.timezone(timezone_str).localize(
        datetime.datetime.fromtimestamp(start_timestamp)
    )

    print("START DATETIME: " + str(start_datetime))

    date_iter = croniter(cron_schedule, start_datetime)

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    next_date = date_iter.get_prev(datetime.datetime)

    while True:
        next_date = to_timezone(
            pendulum.instance(date_iter.get_next(datetime.datetime)), timezone_str
        )

        yield next_date
