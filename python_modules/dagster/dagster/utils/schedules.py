import datetime
from typing import Iterator, Optional

import pendulum
import pytz
from croniter import croniter
from dagster import check
from dagster.seven.compat.pendulum import to_timezone


def schedule_execution_time_iterator(
    start_timestamp: float, cron_schedule: str, execution_timezone: Optional[str]
) -> Iterator[datetime.datetime]:
    timezone_str = execution_timezone if execution_timezone else "UTC"

    utc_datetime = pytz.utc.localize(datetime.datetime.utcfromtimestamp(start_timestamp))
    start_datetime = utc_datetime.astimezone(pytz.timezone(timezone_str))

    date_iter = croniter(cron_schedule, start_datetime)

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    next_date = date_iter.get_prev(datetime.datetime)

    cron_parts = cron_schedule.split(" ")

    check.invariant(len(cron_parts) == 5)

    is_numeric = [part.isnumeric() for part in cron_parts]

    delta_fn = None

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower than adding a fixed interval
    if cron_schedule.endswith(" * *") and all(is_numeric[0:3]):  # monthly
        delta_fn = lambda d, num: d.add(months=num)
        should_hour_change = False
    elif (
        all(is_numeric[0:2]) and is_numeric[4] and cron_parts[2] == "*" and cron_parts[3] == "*"
    ):  # weekly
        delta_fn = lambda d, num: d.add(weeks=num)
        should_hour_change = False
    elif all(is_numeric[0:2]) and cron_schedule.endswith(" * * *"):  # daily
        delta_fn = lambda d, num: d.add(days=num)
        should_hour_change = False
    elif is_numeric[0] and cron_schedule.endswith(" * * * *"):  # hourly
        delta_fn = lambda d, num: d.add(hours=num)
        should_hour_change = True

    if delta_fn:
        # Use pendulums for intervals when possible
        next_date = to_timezone(pendulum.instance(next_date), timezone_str)
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
    else:
        # Otherwise fall back to croniter
        while True:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_next(datetime.datetime)), timezone_str
            )

            yield next_date
