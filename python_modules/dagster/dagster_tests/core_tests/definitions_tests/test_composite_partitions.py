from datetime import datetime

from dagster import DailyPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.composite_partitions import CompositePartitionsDefinition

DATE_FORMAT = "%Y-%m-%d"


def test_composite_static_partitions():
    partitions1 = StaticPartitionsDefinition(["a", "b", "c"])
    partitions2 = StaticPartitionsDefinition(["x", "y", "z"])
    composite = CompositePartitionsDefinition({"abc": partitions1, "xyz": partitions2})
    assert composite.get_partition_keys() == [
        "a|x",
        "a|y",
        "a|z",
        "b|x",
        "b|y",
        "b|z",
        "c|x",
        "c|y",
        "c|z",
    ]


def test_composite_time_window_static_partitions():
    time_window_partitions = DailyPartitionsDefinition(start_date="2021-05-05")
    static_partitions = StaticPartitionsDefinition(["a", "b", "c"])
    composite = CompositePartitionsDefinition(
        {"date": time_window_partitions, "abc": static_partitions}
    )
    assert composite.get_partition_keys(
        current_time=datetime.strptime("2021-05-07", DATE_FORMAT)
    ) == [
        "2021-05-05|a",
        "2021-05-05|b",
        "2021-05-05|c",
        "2021-05-06|a",
        "2021-05-06|b",
        "2021-05-06|c",
    ]
