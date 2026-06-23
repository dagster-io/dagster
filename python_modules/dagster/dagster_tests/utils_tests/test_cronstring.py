import pytest
from dagster._utils.cronstring import get_fixed_minute_interval


@pytest.mark.parametrize(
    "cron_schedule,expected",
    [
        # Basic hourly / minutely schedules have a fixed interval.
        ("0 * * * *", 60),
        ("* * * * *", 1),
        # */N minute schedules that tick throughout every hour of every day, where N
        # divides 60, have a fixed interval.
        ("*/15 * * * *", 15),
        ("*/5 * * * *", 5),
        ("*/30 * * * *", 30),
        ("*/1 * * * *", 1),
        # */N where N does not divide 60 jumps (e.g. :54 -> :07), so no fixed interval.
        ("*/7 * * * *", None),
        ("*/13 * * * *", None),
        # An interval of 60 or more is not a sub-hour fixed interval.
        ("*/60 * * * *", None),
        ("*/0 * * * *", None),
        # A constraint on any field other than the minute field means the gap between
        # ticks is not fixed, so we must return None. Previously these were incorrectly
        # treated as fixed */N schedules. See https://github.com/dagster-io/dagster/issues/33912
        ("*/15 9-16 * * 1-5", None),
        ("*/15 9-16 * * *", None),
        ("*/15 * * * 1-5", None),
        ("*/15 0 * * *", None),
        ("*/15 * 1 * *", None),
        ("*/15 * * 1 *", None),
        # Explicit minute lists that tick every hour of every day are equivalent to */N when the
        # ticks (including the wrap into the next hour) are evenly spaced.
        ("0,30 * * * *", 30),
        ("0,15,30,45 * * * *", 15),
        ("0,20,40 * * * *", 20),
        ("5,35 * * * *", 30),  # evenly spaced even though it does not start at :00
        # Order does not matter -- the minutes are sorted before measuring gaps.
        ("30,0 * * * *", 30),
        ("45,15,0,30 * * * *", 15),
        # Explicit minute lists that are NOT evenly spaced around the hour have no fixed interval.
        ("0,20 * * * *", None),  # gaps of 20 then 40 (40 -> 60/00)
        ("0,30,45 * * * *", None),
        # The expansion of */7: consecutive gaps are all 7, but the wrap (56 -> 00) is 4, so it is
        # NOT a fixed interval -- the wrap gap is what the */7 divisor check rejects.
        ("0,7,14,21,28,35,42,49,56 * * * *", None),
        # Non-wildcard minute fields that are not */N have no fixed interval.
        ("0,15,30,45 9-16 * * 1-5", None),
        ("0 0 * * *", None),
        ("5 * * * *", None),
    ],
)
def test_get_fixed_minute_interval(cron_schedule: str, expected: int | None) -> None:
    assert get_fixed_minute_interval(cron_schedule) == expected


def test_get_fixed_minute_interval_is_order_independent() -> None:
    # A scrambled minute list must yield the same interval as its sorted form. This fails if the
    # implementation stops sorting before measuring gaps (unsorted minutes produce negative gaps,
    # so the scrambled form would return None instead of 15).
    assert (
        get_fixed_minute_interval("45,15,0,30 * * * *")
        == get_fixed_minute_interval("0,15,30,45 * * * *")
        == 15
    )
