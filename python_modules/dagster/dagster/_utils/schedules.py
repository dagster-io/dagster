import datetime
import re
from collections.abc import Iterator, Sequence

from dagster_cron import (
    cron_string_includes as _native_cron_string_includes,
    cron_string_iterator as _native_cron_string_iterator,
    is_valid_cron_string as _native_is_valid_cron_string,
    repeats_every_hour as _native_cron_string_repeats_every_hour,
)

import dagster._check as check
from dagster._time import get_current_datetime

CRON_RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7), (0, 59))
CRON_STEP_SEARCH_REGEX = re.compile(r"^([^-]+)-([^-/]+)(/(\d+))?$")
INT_REGEX = re.compile(r"^\d+$")
CRON_ITERATOR_BATCH_SIZE = 128
CRON_INTERVAL_SAMPLE_SIZE = 1000


def is_valid_cron_string(cron_string: str) -> bool:
    return _native_is_valid_cron_string(cron_string)


def is_valid_cron_schedule(cron_schedule: str | Sequence[str]) -> bool:
    return (
        is_valid_cron_string(cron_schedule)
        if isinstance(cron_schedule, str)
        else len(cron_schedule) > 0
        and all(is_valid_cron_string(cron_string) for cron_string in cron_schedule)
    )


def cron_string_repeats_every_hour(cron_string: str) -> bool:
    """Returns if the given cron schedule repeats every hour."""
    return _native_cron_string_repeats_every_hour(cron_string)


def _has_out_of_range_cron_interval_str(cron_string: str):
    try:
        for i, cron_part in enumerate(cron_string.lower().split()):
            expr_parts = cron_part.split(",")
            while len(expr_parts) > 0:
                expr = expr_parts.pop()
                t = re.sub(
                    r"^\*(\/.+)$",
                    r"%d-%d\1" % (CRON_RANGES[i][0], CRON_RANGES[i][1]),  # noqa: UP031
                    str(expr),
                )
                m = CRON_STEP_SEARCH_REGEX.search(t)
                if not m:
                    # try normalizing "{start}/{step}" to "{start}-{max}/{step}".
                    t = re.sub(
                        r"^(.+)\/(.+)$",
                        r"\1-%d/\2" % (CRON_RANGES[i][1]),  # noqa: UP031
                        str(expr),
                    )
                    m = CRON_STEP_SEARCH_REGEX.search(t)
                if m:
                    (low, high, step) = m.group(1), m.group(2), m.group(4) or 1
                    if i == 2 and high == "l":
                        high = "31"
                    if not INT_REGEX.search(low) or not INT_REGEX.search(high):
                        continue
                    low, high, step = map(int, [low, high, step])
                    if step > high:
                        return True
    except:
        pass
    return False


def has_out_of_range_cron_interval(cron_schedule: str | Sequence[str]):
    """Utility function to detect cron schedules like '*/90 * * * *', which are valid cron schedules
    but which evaluate to once every hour, not once every 90 minutes as might be expected.  This is
    useful to detect so that we can issue warnings or some other kind of feedback to the user.  This
    function does not detect cases where the step does not divide cleanly in the range, which is
    another case that might cause some surprising behavior (e.g. '*/7 * * * *').
    """
    return (
        _has_out_of_range_cron_interval_str(cron_schedule)
        if isinstance(cron_schedule, str)
        else any(_has_out_of_range_cron_interval_str(s) for s in cron_schedule)
    )


def cron_string_iterator(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
    ascending: bool = True,
    start_offset: int = 0,
) -> Iterator[datetime.datetime]:
    for batch in batched_cron_string_iterator(
        start_timestamp, cron_string, execution_timezone, ascending, start_offset
    ):
        yield from batch


def batched_cron_string_iterator(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
    ascending: bool = True,
    start_offset: int = 0,
    batch_size: int = CRON_ITERATOR_BATCH_SIZE,
) -> Iterator[Sequence[datetime.datetime]]:
    iterator = _native_cron_string_iterator(
        start_timestamp, cron_string, execution_timezone, ascending, start_offset
    )
    if batch_size <= 0:
        return

    while True:
        batch = iterator.next_batch(batch_size)
        if not batch:
            return
        yield batch


def cron_string_iterator_batch(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
    count: int,
    ascending: bool = True,
    start_offset: int = 0,
) -> Sequence[datetime.datetime]:
    iterator = _native_cron_string_iterator(
        start_timestamp, cron_string, execution_timezone, ascending, start_offset
    )
    return [] if count <= 0 else iterator.next_batch(count)


def cron_string_includes(
    timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
) -> bool:
    return _native_cron_string_includes(timestamp, cron_string, execution_timezone)


def reverse_cron_string_iterator(
    end_timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
) -> Iterator[datetime.datetime]:
    yield from cron_string_iterator(end_timestamp, cron_string, execution_timezone, ascending=False)


def schedule_execution_time_iterator(
    start_timestamp: float,
    cron_schedule: str | Sequence[str],
    execution_timezone: str | None,
    ascending: bool = True,
) -> Iterator[datetime.datetime]:
    """Generator of execution datetimes >= start_timestamp for the given schedule.

    Here cron_schedule is either a cron string or a sequence of cron strings. In the latter case,
    the next execution datetime is obtained by computing the next cron datetime
    after the current execution datetime for each cron string in the sequence, and then choosing
    the earliest among them.
    """
    check.invariant(
        is_valid_cron_schedule(cron_schedule), desc=f"{cron_schedule} must be a valid cron schedule"
    )

    if isinstance(cron_schedule, str):
        yield from (
            cron_string_iterator(start_timestamp, cron_schedule, execution_timezone)
            if ascending
            else reverse_cron_string_iterator(start_timestamp, cron_schedule, execution_timezone)
        )
    else:
        iterators = [
            (
                cron_string_iterator(start_timestamp, cron_string, execution_timezone)
                if ascending
                else reverse_cron_string_iterator(start_timestamp, cron_string, execution_timezone)
            )
            for cron_string in cron_schedule
        ]
        next_dates = [next(it) for it in iterators]
        while True:
            # Choose earliest (ascending) or latest (descending) out of all subsequent datetimes.
            selected_date = min(next_dates) if ascending else max(next_dates)
            yield selected_date
            # Increment all iterators that generated the selected datetime.
            for i, next_date in enumerate(next_dates):
                if next_date == selected_date:
                    next_dates[i] = next(iterators[i])


def get_latest_completed_cron_tick(
    cron_string: str,
    current_time: datetime.datetime,
    timezone: str | None,
) -> datetime.datetime:
    cron_iter = reverse_cron_string_iterator(
        end_timestamp=current_time.timestamp(),
        cron_string=cron_string,
        execution_timezone=timezone,
    )
    return next(cron_iter)


def get_next_cron_tick(
    cron_string: str,
    current_time: datetime.datetime,
    timezone: str | None,
) -> datetime.datetime:
    cron_iter = cron_string_iterator(
        start_timestamp=current_time.timestamp(),
        cron_string=cron_string,
        execution_timezone=timezone,
    )
    return next(cron_iter)


def get_smallest_cron_interval(
    cron_string: str,
    execution_timezone: str | None = None,
) -> datetime.timedelta:
    """Find the smallest interval between cron ticks for a given cron schedule.

    Uses a sampling-based approach to find the minimum interval by generating
    consecutive cron ticks and measuring the gaps between them. Sampling is capped
    at 1000 generated ticks. The native cron iterator owns the per-step search bound.

    Args:
        cron_string: A cron string
        execution_timezone: Timezone to use for cron evaluation (defaults to UTC)

    Returns:
        The smallest timedelta between any two consecutive cron ticks

    Raises:
        CheckError: If the cron string is invalid or not recognized by Dagster
    """
    check.invariant(
        is_valid_cron_string(cron_string), desc=f"{cron_string} must be a valid cron string"
    )

    execution_timezone = execution_timezone or "UTC"

    # Always start at current time in the specified timezone
    start_time = get_current_datetime(tz=execution_timezone)

    # Start sampling from a year ago to capture seasonal variations (DST, leap years)
    sampling_start = start_time - datetime.timedelta(days=365)

    ticks = cron_string_iterator_batch(
        start_timestamp=sampling_start.timestamp(),
        cron_string=cron_string,
        execution_timezone=execution_timezone,
        count=CRON_INTERVAL_SAMPLE_SIZE,
    )

    if len(ticks) < 2:
        raise ValueError("Could not determine minimum interval from cron schedule")

    prev_tick = ticks[0]
    min_interval = None

    for current_tick in ticks[1:]:
        interval = current_tick - prev_tick

        # Handle DST transitions where two ticks can have the same wall clock time
        # but different fold values (indicating they're actually different points in time)
        if interval == datetime.timedelta(seconds=0):
            # Check if this is a DST ambiguous time scenario where both ticks
            # represent the same local time but different actual moments
            if (
                current_tick.hour == prev_tick.hour
                and current_tick.minute == prev_tick.minute
                and current_tick.second == prev_tick.second
                and current_tick.fold != prev_tick.fold
            ):
                # This is a DST fall-back transition - skip this zero interval
                # as it's not representative of the true minimum cron interval
                prev_tick = current_tick
                continue
            # We've encountered a genuine zero interval (which shouldn't happen)
            raise Exception("Encountered a genuine zero interval")

        if interval < datetime.timedelta(seconds=0):
            # This happens when the sampling encounters a daylight savings transition where the clocks roll back
            # Just skip this interval and continue sampling
            prev_tick = current_tick
            continue

        # Update minimum interval
        if min_interval is None or interval < min_interval:
            min_interval = interval

        prev_tick = current_tick

    if min_interval is None:
        # Fallback - should not happen with valid cron schedules
        raise ValueError("Could not determine minimum interval from cron schedule")

    return min_interval
