from datetime import datetime

import pytest
from dagster import TimeWindow
from dagster._core.storage.db_io_manager import TablePartitionDimension
from dagster_deltalake.io_manager import _time_window_partition_dnf
from deltalake.schema import Field, PrimitiveType, Schema

TablePartitionDimension(
    partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
    partition_expr="my_timestamp_col",
)


@pytest.fixture
def test_schema() -> Schema:
    fields = [
        Field(name="string_col", ty=PrimitiveType("string")),
        Field(name="date_col", ty=PrimitiveType("date")),
        Field(name="timestamp_col", ty=PrimitiveType("timestamp")),
    ]
    return Schema(fields=fields)


def test_time_window_partition_dnf() -> None:
    part = TablePartitionDimension(
        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
        partition_expr="my_timestamp_col",
    )
    dnf = _time_window_partition_dnf(part)
    assert dnf == ("my_timestamp_col", "=", "2020-01-02")
