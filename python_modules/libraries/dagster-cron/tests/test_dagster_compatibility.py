from __future__ import annotations

import datetime as dt
import zoneinfo

import pytest

from dagster_cron import cron_string_iterator, is_valid_cron_string


UTC = dt.timezone.utc


@pytest.mark.parametrize(
    "cron_string",
    [
        "@hourly",
        "@daily",
        "@weekly",
        "@monthly",
        "@yearly",
        "@annually",
        "@midnight",
        "0 0 * * ?",
        "0 0 ? * 1",
        "0 0 L * *",
        "0 0 15W * *",
        "0 0 W15 * *",
        "0 0 * * mon#2",
        "0 0 * * 7",
        "0 0 29 2 *",
        "0 0 * nov-mar *",
        "0 0 * * fri-mon",
        "R * * * *",
    ],
)
def test_supported_dagster_cron_strings(cron_string: str):
    assert is_valid_cron_string(cron_string)


@pytest.mark.parametrize(
    "cron_string",
    [
        "",
        "@reboot",
        "* * * * * *",
        "* * * * * * *",
        "0 0 31 2 *",
        # Unlike croniter iteration, cron considers this valid because the OR-ed day-of-week
        # field still matches Wednesdays in February even though February 30 is impossible.
        # "0 0 30 2 3",
        "H * * * *",
    ],
)
def test_unsupported_dagster_cron_strings(cron_string: str):
    assert not is_valid_cron_string(cron_string)


def test_fold_compatibility_for_non_hourly_schedules():
    timezone = zoneinfo.ZoneInfo("Europe/Berlin")
    iterator = cron_string_iterator(
        dt.datetime(2023, 10, 27, 2, tzinfo=timezone).timestamp(),
        "0 2 * * *",
        "Europe/Berlin",
    )

    assert [next(iterator).timestamp() for _ in range(4)] == [
        dt.datetime(2023, 10, 27, 0, tzinfo=UTC).timestamp(),
        dt.datetime(2023, 10, 28, 0, tzinfo=UTC).timestamp(),
        dt.datetime(2023, 10, 29, 1, tzinfo=UTC).timestamp(),
        dt.datetime(2023, 10, 30, 1, tzinfo=UTC).timestamp(),
    ]


def test_start_offset_matches_dagster_inclusive_boundary_contract():
    iterator = cron_string_iterator(
        dt.datetime(2024, 1, 1, 0, 5, tzinfo=UTC).timestamp(),
        "*/5 * * * *",
        "UTC",
        True,
        -1,
    )

    assert next(iterator) == dt.datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    assert next(iterator) == dt.datetime(2024, 1, 1, 0, 5, tzinfo=UTC)
