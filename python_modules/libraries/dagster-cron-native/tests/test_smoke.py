from __future__ import annotations

import datetime as dt
import importlib.util
import zoneinfo

import pytest

import dagster_cron_native
from dagster_cron_native import (
    CronStringIterator,
    DayMatching,
    DayOfWeekNumbering,
    NonexistentTimeBehavior,
    Schedule,
    ScheduleIterator,
    ScheduleParts,
    cron_string_iterator,
    is_valid_cron_string,
    repeats_every_hour,
)


UTC = dt.timezone.utc


def test_import_exports_native_schedule_api_only():
    assert dagster_cron_native.Schedule is Schedule
    assert dagster_cron_native.ScheduleIterator is ScheduleIterator
    assert dagster_cron_native.CronStringIterator is CronStringIterator
    assert dagster_cron_native.ScheduleParts is ScheduleParts
    assert dagster_cron_native.DayMatching is DayMatching
    assert dagster_cron_native.DayOfWeekNumbering is DayOfWeekNumbering
    assert dagster_cron_native.NonexistentTimeBehavior is NonexistentTimeBehavior
    assert dagster_cron_native.__all__ == [
        "CronStringIterator",
        "DayMatching",
        "DayOfWeekNumbering",
        "NonexistentTimeBehavior",
        "Schedule",
        "ScheduleIterator",
        "ScheduleParts",
        "cron_string_iterator",
        "is_valid_cron_string",
        "repeats_every_hour",
    ]
    assert not hasattr(dagster_cron_native, "croniter")
    assert not hasattr(dagster_cron_native, "croniter_range")
    assert not hasattr(Schedule("* * * * *"), "iterator")
    assert not hasattr(dagster_cron_native, "IteratorDirection")
    assert importlib.util.find_spec("dagster_cron_native.croniter") is None


def test_schedule_source_round_trip():
    schedule = Schedule("*/5 * * * *")

    assert schedule.source() == "*/5 * * * *"


def test_forward_iterator_returns_datetimes():
    schedule = Schedule("*/5 * * * *")
    iterator = schedule.iter(dt.datetime(2024, 1, 1, tzinfo=UTC))

    result = iterator.next()

    assert result == dt.datetime(2024, 1, 1, 0, 5, tzinfo=UTC)


def test_backward_iterator_returns_datetimes():
    schedule = Schedule("*/5 * * * *")
    iterator = schedule.iter(dt.datetime(2024, 1, 1, 0, 10, tzinfo=UTC))

    result = iterator.previous()

    assert result == dt.datetime(2024, 1, 1, 0, 5, tzinfo=UTC)


def test_iterator_exposes_only_forward_next_and_previous():
    iterator = Schedule("*/5 * * * *").iter(dt.datetime(2024, 1, 1, tzinfo=UTC))

    assert hasattr(iterator, "next")
    assert hasattr(iterator, "previous")
    assert hasattr(iterator, "current")
    assert not hasattr(iterator, "current_timestamp")
    assert not hasattr(iterator, "next_timestamp")
    assert not hasattr(iterator, "previous_timestamp")
    assert not hasattr(iterator, "next_forward")
    assert not hasattr(iterator, "next_backward")


def test_numeric_start_times_are_rejected():
    schedule = Schedule("*/5 * * * *")

    with pytest.raises(TypeError, match="datetime or None"):
        schedule.iter(dt.datetime(2024, 1, 1, tzinfo=UTC).timestamp())


def test_six_field_schedule_config():
    schedule = Schedule("*/20 * * * * *", parts=ScheduleParts.SIX)
    iterator = schedule.iter(dt.datetime(2024, 1, 1, tzinfo=UTC))

    assert iterator.next() == dt.datetime(2024, 1, 1, 0, 0, 20, tzinfo=UTC)


def test_typed_schedule_config_enums():
    timezone = zoneinfo.ZoneInfo("America/New_York")
    schedule = Schedule(
        "0 30 2 * * sun",
        parts=ScheduleParts.SIX,
        day_matching=DayMatching.OR,
        day_of_week_numbering=DayOfWeekNumbering.ZERO_INDEXED,
        nonexistent_time_behavior=NonexistentTimeBehavior.NEXT_EXISTENT,
    )
    iterator = schedule.iter(dt.datetime(2024, 3, 9, tzinfo=timezone))

    assert iterator.next() == dt.datetime(2024, 3, 10, 3, tzinfo=timezone)


def test_zoneinfo_datetime_round_trip():
    timezone = zoneinfo.ZoneInfo("America/New_York")
    schedule = Schedule("0 0 3 * * *", parts=ScheduleParts.SIX)
    iterator = schedule.iter(dt.datetime(2024, 3, 9, tzinfo=timezone))

    result = iterator.next()

    assert result == dt.datetime(2024, 3, 9, 3, tzinfo=timezone)
    assert isinstance(result.tzinfo, zoneinfo.ZoneInfo)
    assert result.tzinfo.key == "America/New_York"


def test_includes_uses_supplied_datetime_timezone():
    timezone = zoneinfo.ZoneInfo("Europe/London")
    schedule = Schedule("7 * * * *")

    assert schedule.includes(dt.datetime(2025, 3, 30, 2, 7, tzinfo=timezone))
    assert not schedule.includes(dt.datetime(2025, 3, 30, 2, 8, tzinfo=timezone))


def test_search_years_bounds_iteration():
    schedule = Schedule(
        "0 13 8 1,4,7,10 wed",
        parts=ScheduleParts.FIVE,
        day_matching=DayMatching.AND,
        search_years=1,
    )
    iterator = schedule.iter(dt.datetime(2020, 9, 24, tzinfo=UTC))

    with pytest.raises(ValueError, match="failed to find next date"):
        iterator.next()


def test_string_config_values_are_rejected():
    with pytest.raises(TypeError):
        Schedule("* * * * *", day_matching="and")


def test_dagster_cron_string_iterator_is_inclusive():
    iterator = cron_string_iterator(
        dt.datetime(2024, 1, 1, tzinfo=UTC).timestamp(),
        "0 0 * * *",
        "UTC",
    )

    assert next(iterator) == dt.datetime(2024, 1, 1, tzinfo=UTC)
    assert next(iterator) == dt.datetime(2024, 1, 2, tzinfo=UTC)


def test_dagster_aliases_and_validation():
    assert is_valid_cron_string("@annually")
    assert is_valid_cron_string("@midnight")
    assert not is_valid_cron_string("@reboot")
    assert not is_valid_cron_string("0 0 31 2 *")
    assert repeats_every_hour("@hourly")
    assert repeats_every_hour("15 * * * *")
    assert not repeats_every_hour("@daily")
