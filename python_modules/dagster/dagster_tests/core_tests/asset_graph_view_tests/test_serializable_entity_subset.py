import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset


def test_union():
    a_true = SerializableEntitySubset(key=dg.AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=dg.AssetKey("a"), value=False)

    assert a_true.compute_union(a_false) == a_true
    assert a_false.compute_union(a_true) == a_true
    assert a_true.compute_union(a_true) == a_true
    assert a_false.compute_union(a_false) == a_false

    partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )

    assert b_12.compute_union(b_3) == SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2", "3"]),
    )


def test_intersection():
    a_true = SerializableEntitySubset(key=dg.AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=dg.AssetKey("a"), value=False)

    assert a_true.compute_intersection(a_false) == a_false
    assert a_false.compute_intersection(a_true) == a_false
    assert a_true.compute_intersection(a_true) == a_true
    assert a_false.compute_intersection(a_false) == a_false

    partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )
    b_1 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert b_12.compute_intersection(b_3) == SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.empty_subset(),
    )

    assert b_12.compute_intersection(b_1) == b_1


def test_difference():
    a_true = SerializableEntitySubset(key=dg.AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=dg.AssetKey("a"), value=False)

    assert a_true.compute_difference(a_false) == a_true
    assert a_false.compute_difference(a_true) == a_false
    assert a_true.compute_difference(a_true) == a_false
    assert a_false.compute_difference(a_false) == a_false

    partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )
    b_1 = SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert b_12.compute_difference(b_3) == b_12

    assert b_12.compute_difference(b_1) == SerializableEntitySubset(
        key=dg.AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["2"]),
    )


def test_from_coercible_value():
    a = dg.AssetKey("a")
    partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])

    assert SerializableEntitySubset.from_coercible_value(
        key=a,
        value=None,
        partitions_def=None,
    ) == SerializableEntitySubset(key=dg.AssetKey("a"), value=True)

    assert SerializableEntitySubset.from_coercible_value(
        key=a,
        value="1",
        partitions_def=partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert SerializableEntitySubset.from_coercible_value(
        key=a,
        value=["1", "2"],
        partitions_def=partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )

    assert SerializableEntitySubset.from_coercible_value(
        key=a,
        value=partitions_def.subset_with_partition_keys(["1"]),
        partitions_def=None,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert SerializableEntitySubset.from_coercible_value(
        key=a,
        value=partitions_def.subset_with_partition_keys(["1"]),
        partitions_def=partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    with pytest.raises(CheckError):
        SerializableEntitySubset.from_coercible_value(
            key=a,
            value=partitions_def.subset_with_partition_keys(["1"]),
            partitions_def=dg.DailyPartitionsDefinition(start_date="2024-01-01"),
        )

    with pytest.raises(CheckError):
        SerializableEntitySubset.from_coercible_value(
            key=a,
            value="1",
            partitions_def=None,
        )

    with pytest.raises(CheckError):
        SerializableEntitySubset.from_coercible_value(
            key=a,
            value=None,
            partitions_def=partitions_def,
        )


def test_try_from_coercible_value():
    a = dg.AssetKey("a")
    partitions_def = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value=None,
        partitions_def=None,
    ) == SerializableEntitySubset(key=dg.AssetKey("a"), value=True)

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value="1",
        partitions_def=partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value=["1", "2"],
        partitions_def=partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value=partitions_def.subset_with_partition_keys(["1"]),
        partitions_def=None,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert (
        SerializableEntitySubset.try_from_coercible_value(
            key=a,
            value="1",
            partitions_def=None,
        )
        is None
    )

    assert (
        SerializableEntitySubset.try_from_coercible_value(
            key=a,
            value=None,
            partitions_def=partitions_def,
        )
        is None
    )


def test_from_coercible_time_partitions():
    time_window_partitions_def = dg.DailyPartitionsDefinition(start_date="2024-01-01")
    a = dg.AssetKey("a")

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value=time_window_partitions_def.subset_with_partition_keys(["2024-01-01"]),
        partitions_def=time_window_partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=time_window_partitions_def.subset_with_partition_keys(["2024-01-01"]),
    )

    assert SerializableEntitySubset.try_from_coercible_value(
        key=a,
        value="2024-01-01",
        partitions_def=time_window_partitions_def,
    ) == SerializableEntitySubset(
        key=dg.AssetKey("a"),
        value=time_window_partitions_def.subset_with_partition_keys(["2024-01-01"]),
    )

    with pytest.raises(Exception):
        SerializableEntitySubset.from_coercible_value(
            key=a,
            value="invalid_value",
            partitions_def=time_window_partitions_def,
        )

    assert (
        SerializableEntitySubset.try_from_coercible_value(
            key=a,
            value="invalid_value",
            partitions_def=time_window_partitions_def,
        )
        is None
    )

    with pytest.raises(Exception):
        SerializableEntitySubset.from_coercible_value(
            key=a,
            value="2024-01-01 12:45:45",
            partitions_def=time_window_partitions_def,
        )

    assert (
        SerializableEntitySubset.try_from_coercible_value(
            key=a,
            value="2024-01-01 12:45:45",
            partitions_def=time_window_partitions_def,
        )
        is None
    )

    with pytest.raises(ValueError):
        assert SerializableEntitySubset.from_coercible_value(
            key=a,
            value=["2024-01-01 12:45:45", "2024-01-02"],
            partitions_def=time_window_partitions_def,
        ) == SerializableEntitySubset(
            key=dg.AssetKey("a"),
            value=time_window_partitions_def.subset_with_partition_keys(["2024-01-02"]),
        )


def test_from_coercible_value_dynamic_partitions():
    partitions_def = dg.DynamicPartitionsDefinition(name="test")
    a = dg.AssetKey("a")

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("test", ["1", "2"])

        assert SerializableEntitySubset.from_coercible_value(
            key=a,
            value=["1"],
            partitions_def=partitions_def,
        ) == SerializableEntitySubset(
            key=a,
            value=partitions_def.subset_with_partition_keys(["1"]),
        )

        # Since DynamicPartitionsDefinition use a DefaultPartitionsSubset, it will not validate the partition key,
        # so passing the instance is not necessary
        assert SerializableEntitySubset.from_coercible_value(
            key=a,
            value=["1"],
            partitions_def=partitions_def,
        ) == SerializableEntitySubset(
            key=a,
            value=partitions_def.subset_with_partition_keys(["1"]),
        )

        assert SerializableEntitySubset.from_coercible_value(
            key=a,
            value=["3"],
            partitions_def=partitions_def,
        ) == SerializableEntitySubset(
            key=a,
            value=partitions_def.subset_with_partition_keys(["3"]),
        )
