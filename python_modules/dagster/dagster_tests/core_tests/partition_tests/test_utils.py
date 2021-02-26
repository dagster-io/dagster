from datetime import datetime

import pytest
from dagster import DagsterInvariantViolationError, Partition
from dagster.utils.partitions import DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE, date_partition_range


def test_date_partition_range_out_of_order():
    with pytest.raises(DagsterInvariantViolationError):
        date_partition_range(
            datetime(year=2020, month=1, day=3), datetime(year=2020, month=1, day=1)
        )


@pytest.mark.parametrize(
    "start, end, delta_range, fmt, inclusive, timezone, expected_partitions",
    [
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=1, day=6),
            "days",
            None,
            False,
            None,
            ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"],
        ),
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=1, day=6, hour=1),
            "days",
            None,
            True,
            None,
            ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05", "2020-01-06"],
        ),
        (
            datetime(year=2020, month=12, day=29),
            datetime(year=2021, month=1, day=3),
            "days",
            None,
            False,
            None,
            ["2020-12-29", "2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02"],
        ),
        (
            datetime(year=2020, month=2, day=28),
            datetime(year=2020, month=3, day=3),
            "days",
            None,
            False,
            None,
            ["2020-02-28", "2020-02-29", "2020-03-01", "2020-03-02"],
        ),
        (
            datetime(year=2019, month=2, day=28),
            datetime(year=2019, month=3, day=3),
            "days",
            None,
            False,
            None,
            ["2019-02-28", "2019-03-01", "2019-03-02"],
        ),
        (
            datetime(year=2019, month=2, day=28),
            datetime(year=2019, month=3, day=3),
            "days",
            None,
            False,
            None,
            ["2019-02-28", "2019-03-01", "2019-03-02"],
        ),
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=3, day=6),
            "months",
            None,
            False,
            None,
            ["2020-01-01", "2020-02-01"],
        ),
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=1, day=27),
            "weeks",
            None,
            False,
            None,
            ["2020-01-01", "2020-01-08", "2020-01-15"],
        ),
        (
            datetime(year=2020, month=12, day=1),
            datetime(year=2021, month=2, day=6),
            "months",
            None,
            False,
            None,
            ["2020-12-01", "2021-01-01"],
        ),
        (
            datetime(year=2020, month=2, day=12),
            datetime(year=2020, month=3, day=11),
            "months",
            None,
            False,
            None,
            [],
        ),
        # Daylight savings time partitions
        (
            datetime(year=2019, month=3, day=10, hour=1),
            datetime(year=2019, month=3, day=10, hour=4),
            "hours",
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "UTC",
            [
                "2019-03-10-01:00+0000",
                "2019-03-10-02:00+0000",
                "2019-03-10-03:00+0000",
                "2019-03-10-04:00+0000",
            ],
        ),
        (
            datetime(year=2019, month=3, day=10, hour=1),
            datetime(year=2019, month=3, day=10, hour=4),
            "hours",
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "UTC",
            [
                "2019-03-10-01:00+0000",
                "2019-03-10-02:00+0000",
                "2019-03-10-03:00+0000",
                "2019-03-10-04:00+0000",
            ],
        ),
        (
            datetime(year=2019, month=3, day=10, hour=1),
            datetime(year=2019, month=3, day=10, hour=4),
            "hours",
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "US/Central",
            ["2019-03-10-01:00-0600", "2019-03-10-03:00-0500", "2019-03-10-04:00-0500"],
        ),
        (
            datetime(year=2019, month=11, day=3, hour=0),
            datetime(year=2019, month=11, day=3, hour=3),
            "hours",
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "UTC",
            [
                "2019-11-03-00:00+0000",
                "2019-11-03-01:00+0000",
                "2019-11-03-02:00+0000",
                "2019-11-03-03:00+0000",
            ],
        ),
        (
            datetime(year=2019, month=11, day=3, hour=0),
            datetime(year=2019, month=11, day=3, hour=3),
            "hours",
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            True,
            "US/Central",
            [
                "2019-11-03-00:00-0500",
                "2019-11-03-01:00-0500",
                "2019-11-03-01:00-0600",
                "2019-11-03-02:00-0600",
                "2019-11-03-03:00-0600",
            ],
        ),
    ],
)
def test_date_partition_range(
    start, end, delta_range, fmt, inclusive, timezone, expected_partitions
):

    partition_generator = date_partition_range(
        start,
        end,
        delta_range=delta_range,
        fmt=fmt,
        inclusive=inclusive,
        timezone=timezone,
    )
    generated_partitions = partition_generator()

    assert all(
        isinstance(generated_partition, Partition) for generated_partition in generated_partitions
    )

    assert len(generated_partitions) == len(expected_partitions)
    assert all(
        expected_partition_name == generated_partition_name
        for expected_partition_name, generated_partition_name in zip(
            expected_partitions, [partition.name for partition in generated_partitions]
        )
    )
