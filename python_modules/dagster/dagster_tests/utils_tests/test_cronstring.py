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
        # Non-wildcard minute fields that are not */N have no fixed interval.
        ("0,15,30,45 9-16 * * 1-5", None),
        ("0 0 * * *", None),
        ("5 * * * *", None),
    ],
)
def test_get_fixed_minute_interval(cron_schedule: str, expected: int | None) -> None:
    assert get_fixed_minute_interval(cron_schedule) == expected
