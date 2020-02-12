from datetime import datetime, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from dagster import DagsterInvariantViolationError, Partition
from dagster.utils.partitions import date_partition_range


def test_date_partition_range_out_of_order():
    with pytest.raises(DagsterInvariantViolationError):
        date_partition_range(
            datetime(year=2020, month=1, day=3), datetime(year=2020, month=1, day=1)
        )


@pytest.mark.parametrize(
    'start, end, delta, expected_partitions',
    [
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=1, day=6),
            timedelta(days=1),
            ['2020-01-01', '2020-01-02', '2020-01-03', '2020-01-04'],
        ),
        (
            datetime(year=2020, month=12, day=29),
            datetime(year=2021, month=1, day=3),
            timedelta(days=1),
            ['2020-12-29', '2020-12-30', '2020-12-31', '2021-01-01'],
        ),
        (
            datetime(year=2020, month=2, day=28),
            datetime(year=2020, month=3, day=3),
            timedelta(days=1),
            ['2020-02-28', '2020-02-29', '2020-03-01'],
        ),
        (
            datetime(year=2019, month=2, day=28),
            datetime(year=2019, month=3, day=3),
            timedelta(days=1),
            ['2019-02-28', '2019-03-01'],
        ),
        (
            datetime(year=2020, month=1, day=1),
            datetime(year=2020, month=3, day=6),
            relativedelta(months=1),
            ['2020-01-01', '2020-02-01'],
        ),
        (
            datetime(year=2020, month=12, day=1),
            datetime(year=2021, month=2, day=6),
            relativedelta(months=1),
            ['2020-12-01', '2021-01-01'],
        ),
        (
            datetime(year=2020, month=2, day=12),
            datetime(year=2020, month=3, day=11),
            relativedelta(months=1),
            [],
        ),
    ],
)
def test_date_partition_range_daily(start, end, delta, expected_partitions):
    partition_generator = date_partition_range(start, end, delta)
    generated_partitions = partition_generator()
    assert all(
        isinstance(generated_partition, Partition) for generated_partition in generated_partitions
    )
    assert len(generated_partitions) == len(expected_partitions)
    assert all(
        expected_partition_name == generated_partition_name
        for expected_partition_name, generated_partition_name in zip(
            expected_partitions,
            [generated_partition.name for generated_partition in generated_partitions],
        )
    )
