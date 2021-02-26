import datetime

import pendulum
from croniter import croniter
from dagster import check
from dagster.seven import to_timezone


def schedule_execution_time_iterator(start_timestamp, cron_schedule, execution_timezone):
    check.float_param(start_timestamp, "start_timestamp")
    check.str_param(cron_schedule, "cron_schedule")
    check.opt_str_param(execution_timezone, "execution_timezone")
    timezone_str = execution_timezone if execution_timezone else pendulum.now().timezone.name

    start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

    date_iter = croniter(cron_schedule, start_datetime)

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    next_date = to_timezone(pendulum.instance(date_iter.get_prev(datetime.datetime)), timezone_str)

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

    while True:
        if delta_fn:
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
        else:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_next(datetime.datetime)), timezone_str
            )

        yield next_date
