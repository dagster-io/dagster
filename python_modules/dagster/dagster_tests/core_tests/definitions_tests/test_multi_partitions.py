from datetime import datetime

import pytest

from dagster import (
    AssetKey,
    DagsterEventType,
    DailyPartitionsDefinition,
    EventRecordsFilter,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    repository,
)
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import get_multidimensional_partition_tag
from dagster._core.test_utils import instance_for_test

DATE_FORMAT = "%Y-%m-%d"


def test_invalid_chars():
    valid_partitions = StaticPartitionsDefinition(["x", "y", "z"])
    with pytest.raises(DagsterInvalidDefinitionError):
        MultiPartitionsDefinition(
            {"abc": StaticPartitionsDefinition(["aasdasd|asdas"]), "blah": valid_partitions}
        )
    with pytest.raises(DagsterInvalidDefinitionError):
        MultiPartitionsDefinition(
            {"abc": StaticPartitionsDefinition(["aasas[asdas"]), "blah": valid_partitions}
        )
    with pytest.raises(DagsterInvalidDefinitionError):
        MultiPartitionsDefinition(
            {"abc": StaticPartitionsDefinition(["aasas]asdas"]), "blah": valid_partitions}
        )
    with pytest.raises(DagsterInvalidDefinitionError):
        MultiPartitionsDefinition(
            {"abc": StaticPartitionsDefinition(["asda", "a,s"]), "blah": valid_partitions}
        )


def test_multi_static_partitions():
    partitions1 = StaticPartitionsDefinition(["a", "b", "c"])
    partitions2 = StaticPartitionsDefinition(["x", "y", "z"])
    composite = MultiPartitionsDefinition({"abc": partitions1, "xyz": partitions2})
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


def test_multi_dimensional_time_window_static_partitions():
    time_window_partitions = DailyPartitionsDefinition(start_date="2021-05-05")
    static_partitions = StaticPartitionsDefinition(["a", "b", "c"])
    composite = MultiPartitionsDefinition(
        {"date": time_window_partitions, "abc": static_partitions}
    )
    assert set(
        composite.get_partition_keys(current_time=datetime.strptime("2021-05-07", DATE_FORMAT))
    ) == {
        "a|2021-05-05",
        "b|2021-05-05",
        "c|2021-05-05",
        "a|2021-05-06",
        "b|2021-05-06",
        "c|2021-05-06",
    }

    partitions = composite.get_partitions(current_time=datetime.strptime("2021-05-07", DATE_FORMAT))
    assert len(partitions) == 6
    assert partitions[0].value.get("date").name == "2021-05-05"
    assert partitions[0].value.get("abc").name == "a"


def test_tags_multi_dimensional_partitions():
    time_window_partitions = DailyPartitionsDefinition(start_date="2021-05-05")
    static_partitions = StaticPartitionsDefinition(["a", "b", "c"])
    composite = MultiPartitionsDefinition(
        {"date": time_window_partitions, "abc": static_partitions}
    )

    @asset(partitions_def=composite)
    def asset1():
        return 1

    @asset(partitions_def=composite)
    def asset2(asset1):  # pylint: disable=unused-argument
        return 2

    @repository
    def my_repo():
        return [asset1, asset2, define_asset_job("my_job", partitions_def=composite)]

    with instance_for_test() as instance:
        result = (
            my_repo()
            .get_job("my_job")
            .execute_in_process(
                partition_key=MultiPartitionKey({"abc": "a", "date": "2021-06-01"}),
                instance=instance,
            )
        )
        assert result.success
        assert result.dagster_run.tags[get_multidimensional_partition_tag("abc")] == "a"
        assert result.dagster_run.tags[get_multidimensional_partition_tag("date")] == "2021-06-01"

        materializations = sorted(
            instance.get_event_records(EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION)),
            key=lambda x: x.event_log_entry.dagster_event.asset_key,
        )
        assert len(materializations) == 2

        for materialization in materializations:
            assert materialization.event_log_entry.dagster_event.partition == MultiPartitionKey(
                {"abc": "a", "date": "2021-06-01"}
            )

        materializations = list(
            instance.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey("asset1"),
                    tags={get_multidimensional_partition_tag("abc"): "a"},
                )
            )
        )
        assert len(materializations) == 1

        materializations = list(
            instance.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey("asset1"),
                    tags={get_multidimensional_partition_tag("abc"): "nonexistent"},
                )
            )
        )
        assert len(materializations) == 0

        materializations = list(
            instance.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey("asset1"),
                    tags={get_multidimensional_partition_tag("date"): "2021-06-01"},
                )
            )
        )
        assert len(materializations) == 1
        materializations = list(
            instance.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey("asset2"),
                    tags={get_multidimensional_partition_tag("date"): "2021-06-01"},
                )
            )
        )
        assert len(materializations) == 1
