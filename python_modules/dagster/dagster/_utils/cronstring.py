from itertools import pairwise


def is_basic_daily(cron_schedule: str) -> bool:
    return cron_schedule == "0 0 * * *"


def is_basic_hourly(cron_schedule: str) -> bool:
    return cron_schedule == "0 * * * *"


def is_basic_minutely(cron_schedule: str) -> bool:
    return cron_schedule == "* * * * *"


def get_fixed_minute_interval(cron_schedule: str) -> int | None:
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

    # Every field other than the minute field must be a wildcard. Otherwise the gap between ticks is
    # not a fixed number of minutes (e.g. a restricted hour creates a large gap at the hour boundary).
    if not all(is_wildcard[1:]):
        return None

    minute_field = cron_parts[0]

    # Every-n-minutes form like "*/15".
    if minute_field.startswith("*/"):
        # interval makes up the characters after the "*/"
        interval_str = minute_field[2:]
        if not interval_str.isdigit():
            return None
        interval = int(interval_str)

        # cronstrings like */7 do not have a fixed interval because they jump
        # from :54 to :07, but divisors of 60 do
        if interval > 0 and interval < 60 and 60 % interval == 0:
            return interval

        return None

    # Explicit minute list like "0,30" or "5,35" or "0,15,30,45". Every higher field is a wildcard,
    # so the schedule repeats every hour and has a fixed interval exactly when the ticks are evenly
    # spaced -- including the wrap from the last tick back to the first tick of the next hour. The
    # gaps always sum to 60, so if they're all equal the common gap is 60/k and therefore divides
    # 60; that's why (unlike the */N branch) no separate divisor check is needed. "0,30" -> 30.
    if "," in minute_field:
        parts = minute_field.split(",")
        # isdigit() also rules out negatives and empty fields (e.g. a trailing comma).
        if not all(part.isdigit() for part in parts):
            return None
        minutes = sorted(int(part) for part in parts)

        if len(minutes) < 2 or minutes[-1] > 59:
            return None

        gaps = {later - earlier for earlier, later in pairwise(minutes)}
        gaps.add((60 - minutes[-1]) + minutes[0])  # wrap-around gap into the next hour
        if len(gaps) == 1:
            return next(iter(gaps))

        return None

    return None
