from datetime import datetime
from typing import cast

import pendulum
from dagster import (
    DailyPartitionsDefinition,
    PartitionKeyRange,
)
from dagster._core.definitions.time_window_partitions import (
    PartitionRangeStatus,
    PartitionTimeWindowStatus,
    TimeWindow,
    fetch_flattened_time_window_ranges,
)

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(
        cast(datetime, pendulum.parser.parse(start)), cast(datetime, pendulum.parser.parse(end))
    )


def _check_flatten_time_window_ranges(subsets, expected_result):
    ranges = fetch_flattened_time_window_ranges(subsets)
    assert ranges == [
        PartitionTimeWindowStatus(time_window(window["start"], window["end"]), window["status"])
        for window in expected_result
    ]


partitions_def = DailyPartitionsDefinition(start_date="2021-12-01")
empty_subset = partitions_def.empty_subset()


def test_no_overlap() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-06", "2022-01-06")
            ),
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-06",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-06", "end": "2022-01-07", "status": PartitionRangeStatus.FAILED},
        ],
    )

    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-06", "2022-01-06")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-8", "2022-01-09")
            ),
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-06",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-06", "end": "2022-01-07", "status": PartitionRangeStatus.FAILED},
            {
                "start": "2022-01-08",
                "end": "2022-01-10",
                "status": PartitionRangeStatus.MATERIALIZING,
            },
        ],
    )


def test_overlapped() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-05", "2022-01-06")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-05",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-05", "end": "2022-01-07", "status": PartitionRangeStatus.FAILED},
        ],
    )

    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-05", "2022-01-06")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-06",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-06",
                "end": "2022-01-07",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )


def test_materialized_spans_failed() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-10")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-05", "2022-01-06")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-05",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-05", "end": "2022-01-07", "status": PartitionRangeStatus.FAILED},
            {
                "start": "2022-01-07",
                "end": "2022-01-11",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )


def test_materialized_spans_many_failed() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-01", "2022-12-10")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-05", "2022-01-06")
            )
            .with_partition_key_range(PartitionKeyRange("2022-03-01", "2022-03-10"))
            .with_partition_key_range(PartitionKeyRange("2022-09-01", "2022-10-01")),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-01",
                "end": "2022-01-05",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-01-05",
                "end": "2022-01-07",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-07",
                "end": "2022-03-01",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-03-01",
                "end": "2022-03-11",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-03-11",
                "end": "2022-09-01",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-09-01",
                "end": "2022-10-02",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-10-02",
                "end": "2022-12-11",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )


def test_empty() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset,
            PartitionRangeStatus.FAILED: empty_subset,
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [],
    )

    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-10")
            ).with_partition_key_range(PartitionKeyRange("2022-01-20", "2022-02-10")),
            PartitionRangeStatus.FAILED: empty_subset,
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-11",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-01-20",
                "end": "2022-02-11",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )

    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset,
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-10")
            ).with_partition_key_range(PartitionKeyRange("2022-01-20", "2022-02-10")),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-11",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-20",
                "end": "2022-02-11",
                "status": PartitionRangeStatus.FAILED,
            },
        ],
    )

    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset,
            PartitionRangeStatus.FAILED: empty_subset,
            PartitionRangeStatus.MATERIALIZING: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-10")
            ).with_partition_key_range(PartitionKeyRange("2022-01-20", "2022-02-10")),
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-11",
                "status": PartitionRangeStatus.MATERIALIZING,
            },
            {
                "start": "2022-01-20",
                "end": "2022-02-11",
                "status": PartitionRangeStatus.MATERIALIZING,
            },
        ],
    )


def test_cancels_out() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ).with_partition_key_range(PartitionKeyRange("2022-01-12", "2022-01-13")),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {
                "start": "2022-01-02",
                "end": "2022-01-06",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-12",
                "end": "2022-01-14",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )


def test_lots() -> None:
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            )
            .with_partition_key_range(PartitionKeyRange("2022-01-12", "2022-01-13"))
            .with_partition_key_range(PartitionKeyRange("2022-01-15", "2022-01-17"))
            .with_partition_key_range(PartitionKeyRange("2022-01-19", "2022-01-20"))
            .with_partition_key_range(PartitionKeyRange("2022-01-22", "2022-01-24")),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2021-12-30", "2021-12-31")
            )  # before materialized subset
            .with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-03")
            )  # within materialized subset
            .with_partition_key_range(
                PartitionKeyRange("2022-01-05", "2022-01-06")
            )  # directly after materialized subset
            .with_partition_key_range(
                PartitionKeyRange("2022-01-08", "2022-01-09")
            )  # between materialized subsets
            .with_partition_key_range(
                PartitionKeyRange("2022-01-11", "2022-01-14")
            )  # encompasses materialized subset
            .with_partition_keys(["2022-01-20"])  # at end materialized subset
            .with_partition_keys(
                ["2022-01-22", "2022-01-24"]
            ),  # multiple overlaps within same materialized range
            PartitionRangeStatus.MATERIALIZING: empty_subset,
        },
        [
            {"start": "2021-12-30", "end": "2022-01-01", "status": PartitionRangeStatus.FAILED},
            {"start": "2022-01-02", "end": "2022-01-04", "status": PartitionRangeStatus.FAILED},
            {
                "start": "2022-01-04",
                "end": "2022-01-05",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-05", "end": "2022-01-07", "status": PartitionRangeStatus.FAILED},
            {"start": "2022-01-08", "end": "2022-01-10", "status": PartitionRangeStatus.FAILED},
            {"start": "2022-01-11", "end": "2022-01-15", "status": PartitionRangeStatus.FAILED},
            {
                "start": "2022-01-15",
                "end": "2022-01-18",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-01-19",
                "end": "2022-01-20",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-20", "end": "2022-01-21", "status": PartitionRangeStatus.FAILED},
            {"start": "2022-01-22", "end": "2022-01-23", "status": PartitionRangeStatus.FAILED},
            {
                "start": "2022-01-23",
                "end": "2022-01-24",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {"start": "2022-01-24", "end": "2022-01-25", "status": PartitionRangeStatus.FAILED},
        ],
    )


def test_multiple_overlap_types():
    _check_flatten_time_window_ranges(
        {
            PartitionRangeStatus.MATERIALIZED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-01", "2022-01-06")
            ),
            PartitionRangeStatus.FAILED: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-02", "2022-01-05")
            ),
            PartitionRangeStatus.MATERIALIZING: empty_subset.with_partition_key_range(
                PartitionKeyRange("2022-01-03", "2022-01-04")
            ),
        },
        [
            {
                "start": "2022-01-01",
                "end": "2022-01-02",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
            {
                "start": "2022-01-02",
                "end": "2022-01-03",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-03",
                "end": "2022-01-05",
                "status": PartitionRangeStatus.MATERIALIZING,
            },
            {
                "start": "2022-01-05",
                "end": "2022-01-06",
                "status": PartitionRangeStatus.FAILED,
            },
            {
                "start": "2022-01-06",
                "end": "2022-01-07",
                "status": PartitionRangeStatus.MATERIALIZED,
            },
        ],
    )
