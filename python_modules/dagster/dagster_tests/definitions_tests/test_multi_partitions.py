from datetime import datetime

import pytest
from dagster import (
    AssetKey,
    DagsterEventType,
    DailyPartitionsDefinition,
    EventRecordsFilter,
    IOManager,
    MultiPartitionKey,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    materialize,
    repository,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
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


multipartitions_def = MultiPartitionsDefinition(
    {
        "date": DailyPartitionsDefinition(start_date="2015-01-01"),
        "static": StaticPartitionsDefinition(["a", "b", "c", "d"]),
    }
)


def test_multipartitions_backcompat_subset_serialization():
    partitions1 = StaticPartitionsDefinition(["a", "b", "c"])
    partitions2 = StaticPartitionsDefinition(["x", "y", "z"])
    composite = MultiPartitionsDefinition({"abc": partitions1, "xyz": partitions2})

    partition_keys = [
        MultiPartitionKey({"abc": "a", "xyz": "x"}),
        MultiPartitionKey({"abc": "c", "xyz": "z"}),
    ]
    serialization = '["a|x", "c|z"]'
    assert composite.deserialize_subset(serialization).get_partition_keys() == set(partition_keys)

    version_1_serialization = '{"version": 1, "subset": ["a|x", "c|z"]}'
    assert composite.deserialize_subset(version_1_serialization).get_partition_keys() == set(
        partition_keys
    )


def test_multipartitions_subset_serialization():
    partitions1 = StaticPartitionsDefinition(["a", "b", "c"])
    partitions2 = StaticPartitionsDefinition(["x", "y", "z"])
    composite = MultiPartitionsDefinition({"abc": partitions1, "xyz": partitions2})

    partition_keys = [
        MultiPartitionKey({"abc": "a", "xyz": "x"}),
        MultiPartitionKey({"abc": "c", "xyz": "z"}),
    ]
    assert composite.deserialize_subset(
        composite.empty_subset().with_partition_keys(partition_keys).serialize()
    ).get_partition_keys() == set(partition_keys)


def test_multipartitions_subset_equality():
    assert multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "a", "date": "2015-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    ) == multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "a", "date": "2015-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    )

    assert multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "c", "date": "2015-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    ) != multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "a", "date": "2015-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    )

    assert multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "a", "date": "2015-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    ) != multipartitions_def.empty_subset().with_partition_keys(
        [
            MultiPartitionKey({"static": "a", "date": "2016-01-01"}),
            MultiPartitionKey({"static": "b", "date": "2015-01-05"}),
        ]
    )


@pytest.mark.parametrize(
    "initial, added",
    [
        (["------", "+-----", "------", "------"], ["+-----", "+-----", "------", "------"]),
        (
            ["+--+--", "------", "------", "------"],
            ["+-----", "------", "------", "------"],
        ),
        (
            ["+------", "-+-----", "-++--+-", "+-+++++"],
            ["-+-----", "-+-----", "+-+-+-+", "+++----"],
        ),
        (
            ["+-----+", "------+", "-+++---", "-------"],
            ["+++++++", "-+-+-+-", "-++----", "----+++"],
        ),
    ],
)
def test_multipartitions_subset_addition(initial, added):
    assert len(initial) == len(added)

    static_keys = ["a", "b", "c", "d"]
    daily_partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    multipartitions_def = MultiPartitionsDefinition(
        {
            "date": daily_partitions_def,
            "static": StaticPartitionsDefinition(static_keys),
        }
    )
    full_date_set_keys = daily_partitions_def.get_partition_keys(
        current_time=datetime(year=2015, month=1, day=30)
    )[: max(len(keys) for keys in initial)]
    current_day = datetime.strptime(
        daily_partitions_def.get_partition_keys(current_time=datetime(year=2015, month=1, day=30))[
            : max(len(keys) for keys in initial) + 1
        ][-1],
        daily_partitions_def.fmt,
    )

    initial_subset_keys = []
    added_subset_keys = []
    expected_keys_not_in_updated_subset = []
    for i in range(len(initial)):
        for j in range(len(initial[i])):
            if initial[i][j] == "+":
                initial_subset_keys.append(
                    MultiPartitionKey({"date": full_date_set_keys[j], "static": static_keys[i]})
                )

            if added[i][j] == "+":
                added_subset_keys.append(
                    MultiPartitionKey({"date": full_date_set_keys[j], "static": static_keys[i]})
                )

            if initial[i][j] != "+" and added[i][j] != "+":
                expected_keys_not_in_updated_subset.append(
                    MultiPartitionKey({"date": full_date_set_keys[j], "static": static_keys[i]})
                )

    initial_subset = multipartitions_def.empty_subset().with_partition_keys(initial_subset_keys)
    added_subset = initial_subset.with_partition_keys(added_subset_keys)

    assert initial_subset.get_partition_keys(current_time=current_day) == set(initial_subset_keys)
    assert added_subset.get_partition_keys(current_time=current_day) == set(
        added_subset_keys + initial_subset_keys
    )
    assert added_subset.get_partition_keys_not_in_subset(current_time=current_day) == set(
        expected_keys_not_in_updated_subset
    )


def test_asset_partition_key_is_multipartition_key():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert isinstance(context.asset_partition_key, MultiPartitionKey)

        def load_input(self, context):
            assert isinstance(context.asset_partition_key, MultiPartitionKey)
            return 1

    partitions_def = MultiPartitionsDefinition(
        {"a": StaticPartitionsDefinition(["a"]), "b": StaticPartitionsDefinition(["b"])}
    )

    @asset(
        partitions_def=partitions_def,
        io_manager_key="my_io_manager",
    )
    def my_asset(context):
        return 1

    @asset(
        partitions_def=partitions_def,
        io_manager_key="my_io_manager",
    )
    def asset2(context, my_asset):
        return 2

    materialize(
        [my_asset, asset2],
        resources={"my_io_manager": MyIOManager()},
        partition_key="a|b",
    )


def test_keys_with_dimension_value():
    static_keys = ["a", "b", "c", "d"]
    daily_partitions_def = DailyPartitionsDefinition(start_date="2015-01-01")
    multipartitions_def = MultiPartitionsDefinition(
        {
            "date": daily_partitions_def,
            "static": StaticPartitionsDefinition(static_keys),
        }
    )

    assert multipartitions_def.get_multipartition_keys_with_dimension_value(
        "static", "a", current_time=datetime(year=2015, month=1, day=5)
    ) == [
        MultiPartitionKey({"static": val[0], "date": val[1]})
        for val in [
            ("a", "2015-01-01"),
            ("a", "2015-01-02"),
            ("a", "2015-01-03"),
            ("a", "2015-01-04"),
        ]
    ]
    print(
        multipartitions_def.get_multipartition_keys_with_dimension_value(
            "date", "2015-01-01", current_time=datetime(year=2015, month=1, day=5)
        )
    )
    assert multipartitions_def.get_multipartition_keys_with_dimension_value(
        "date", "2015-01-01", current_time=datetime(year=2015, month=1, day=5)
    ) == [
        MultiPartitionKey({"static": val[0], "date": val[1]})
        for val in [
            ("a", "2015-01-01"),
            ("b", "2015-01-01"),
            ("c", "2015-01-01"),
            ("d", "2015-01-01"),
        ]
    ]
