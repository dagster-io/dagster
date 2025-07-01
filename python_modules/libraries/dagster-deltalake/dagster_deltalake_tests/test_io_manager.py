from datetime import datetime

import pytest
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import TablePartitionDimension
from dagster_deltalake.handler import partition_dimensions_to_dnf
from deltalake.schema import Field, PrimitiveType, Schema

TablePartitionDimension(
    partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
    partition_expr="my_timestamp_col",
)


@pytest.fixture
def test_schema() -> Schema:
    fields = [
        Field(name="string_col", type=PrimitiveType("string")),
        Field(name="date_col", type=PrimitiveType("date")),
        Field(name="timestamp_col", type=PrimitiveType("timestamp")),
    ]
    return Schema(fields=fields)


def test_partition_dimensions_to_dnf(test_schema) -> None:
    parts = [
        TablePartitionDimension(
            partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
            partition_expr="timestamp_col",
        )
    ]
    dnf = partition_dimensions_to_dnf(parts, test_schema, True)
    assert dnf == [("timestamp_col", "=", "2020-01-02 00:00:00")]

    parts = [
        TablePartitionDimension(
            partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
            partition_expr="date_col",
        )
    ]
    dnf = partition_dimensions_to_dnf(parts, test_schema, True)
    assert dnf == [("date_col", "=", "2020-01-02")]
