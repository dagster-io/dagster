from typing import Optional


def is_basic_daily(cron_schedule: str) -> bool:
    return cron_schedule == "0 0 * * *"


def is_basic_hourly(cron_schedule: str) -> bool:
    return cron_schedule == "0 * * * *"


def is_basic_minutely(cron_schedule: str) -> bool:
    return cron_schedule == "* * * * *"


def get_fixed_minute_interval(cron_schedule: str) -> Optional[int]:
    """Given a cronstring, returns whether or not it is safe to
    assume there is a fixed number of minutes between every tick. For
    many cronstrings this is not the case due to Daylight Savings Time,
    but for basic hourly cron schedules and cron schedules like */15 it
    is safe to assume that there are a fixed number of minutes between each
    tick.
    """
    if is_basic_hourly(cron_schedule):
        return 60

    if is_basic_minutely(cron_schedule):
        return 1

    cron_parts = cron_schedule.split()
    is_wildcard = [part == "*" for part in cron_parts]

    # To match this criteria, every other field besides the first must end in *
    # since it must be an every-n-minutes cronstring like */15
    if not is_wildcard[1:]:
        return None

    if not cron_parts[0].startswith("*/"):
        return None

    try:
        # interval makes up the characters after the "*/"
        interval = int(cron_parts[0][2:])
    except ValueError:
        return None

    # cronstrings like */7 do not have a fixed interval because they jump
    # from :54 to :07, but divisors of 60 do
    if interval > 0 and interval < 60 and 60 % interval == 0:
        return interval

    return None
