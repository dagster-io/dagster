from dagster import AssetDep, Definitions, asset
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.partition_mapping import StaticPartitionMapping
from dagster._core.instance import DagsterInstance
from dagster._time import create_datetime


def test_basic_construction_and_identity() -> None:
    @asset
    def an_asset() -> None: ...

    defs = Definitions([an_asset])
    instance = DagsterInstance.ephemeral()
    effective_dt = create_datetime(2020, 1, 1)
    last_event_id = 928348343
    asset_graph_view_t0 = AssetGraphView.for_test(defs, instance, effective_dt, last_event_id)

    assert asset_graph_view_t0
    assert asset_graph_view_t0.effective_dt == effective_dt
    assert asset_graph_view_t0.last_event_id == last_event_id

    # hiding stale resolver deliberately but want to test instance object identity
    assert asset_graph_view_t0._stale_resolver.instance_queryer.instance is instance  # noqa: SLF001

    assert asset_graph_view_t0.asset_graph.all_asset_keys == {an_asset.key}


def test_subset_traversal_static_partitions() -> None:
    number_keys = {"1", "2", "3"}
    letter_keys = {"a", "b", "c"}
    number_static_partitions_def = StaticPartitionsDefinition(list(number_keys))
    letter_static_partitions_def = StaticPartitionsDefinition(list(letter_keys))
    mapping = StaticPartitionMapping({"1": "a", "2": "b", "3": "c"})

    @asset(partitions_def=number_static_partitions_def)
    def up_numbers() -> None: ...

    @asset(
        deps=[AssetDep(up_numbers, partition_mapping=mapping)],
        partitions_def=letter_static_partitions_def,
    )
    def down_letters() -> None: ...

    defs = Definitions([up_numbers, down_letters])
    instance = DagsterInstance.ephemeral()

    asset_graph_view_t0 = AssetGraphView.for_test(defs, instance)
    assert (
        asset_graph_view_t0.get_full_subset(key=up_numbers.key).expensively_compute_partition_keys()
        == number_keys
    )
    assert (
        asset_graph_view_t0.get_full_subset(
            key=down_letters.key
        ).expensively_compute_partition_keys()
        == letter_keys
    )

    # from full up to down
    up_subset = asset_graph_view_t0.get_full_subset(key=up_numbers.key)
    assert up_subset.expensively_compute_partition_keys() == {"1", "2", "3"}
    assert up_subset.compute_child_subset(
        down_letters.key
    ).expensively_compute_partition_keys() == {
        "a",
        "b",
        "c",
    }

    # from full up to down
    down_subset = asset_graph_view_t0.get_full_subset(key=down_letters.key)
    assert down_subset.expensively_compute_partition_keys() == {"a", "b", "c"}
    assert down_subset.compute_parent_subset(
        up_numbers.key
    ).expensively_compute_partition_keys() == {
        "1",
        "2",
        "3",
    }

    # subset of up to subset of down
    assert up_subset.compute_intersection_with_partition_keys({"2"}).compute_child_subset(
        down_letters.key
    ).expensively_compute_partition_keys() == {"b"}

    # subset of down to subset of up
    assert down_subset.compute_intersection_with_partition_keys({"b"}).compute_parent_subset(
        up_numbers.key
    ).expensively_compute_partition_keys() == {"2"}


def test_only_partition_keys() -> None:
    number_keys = {"1", "2", "3"}
    number_static_partitions_def = StaticPartitionsDefinition(list(number_keys))

    @asset(partitions_def=number_static_partitions_def)
    def up_numbers() -> None: ...

    defs = Definitions([up_numbers])
    instance = DagsterInstance.ephemeral()

    asset_graph_view_t0 = AssetGraphView.for_test(defs, instance)

    assert asset_graph_view_t0.get_full_subset(
        key=up_numbers.key
    ).compute_intersection_with_partition_keys({"1", "2"}).expensively_compute_partition_keys() == {
        "1",
        "2",
    }

    assert asset_graph_view_t0.get_full_subset(
        key=up_numbers.key
    ).compute_intersection_with_partition_keys({"3"}).expensively_compute_partition_keys() == set(
        ["3"]
    )
