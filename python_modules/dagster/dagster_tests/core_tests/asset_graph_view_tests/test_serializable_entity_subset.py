from dagster import AssetKey, StaticPartitionsDefinition
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset


def test_union():
    a_true = SerializableEntitySubset(key=AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=AssetKey("a"), value=False)

    assert a_true.compute_union(a_false) == a_true
    assert a_false.compute_union(a_true) == a_true
    assert a_true.compute_union(a_true) == a_true
    assert a_false.compute_union(a_false) == a_false

    partitions_def = StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )

    assert b_12.compute_union(b_3) == SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2", "3"]),
    )


def test_intersection():
    a_true = SerializableEntitySubset(key=AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=AssetKey("a"), value=False)

    assert a_true.compute_intersection(a_false) == a_false
    assert a_false.compute_intersection(a_true) == a_false
    assert a_true.compute_intersection(a_true) == a_true
    assert a_false.compute_intersection(a_false) == a_false

    partitions_def = StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )
    b_1 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert b_12.compute_intersection(b_3) == SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.empty_subset(),
    )

    assert b_12.compute_intersection(b_1) == b_1


def test_difference():
    a_true = SerializableEntitySubset(key=AssetKey("a"), value=True)
    a_false = SerializableEntitySubset(key=AssetKey("a"), value=False)

    assert a_true.compute_difference(a_false) == a_true
    assert a_false.compute_difference(a_true) == a_false
    assert a_true.compute_difference(a_true) == a_false
    assert a_false.compute_difference(a_false) == a_false

    partitions_def = StaticPartitionsDefinition(["1", "2", "3", "4"])

    b_12 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1", "2"]),
    )
    b_3 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["3"]),
    )
    b_1 = SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["1"]),
    )

    assert b_12.compute_difference(b_3) == b_12

    assert b_12.compute_difference(b_1) == SerializableEntitySubset(
        key=AssetKey("b"),
        value=partitions_def.subset_with_partition_keys(["2"]),
    )
