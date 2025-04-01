from typing import cast

import pytest
from dagster import (
    AssetDep,
    DailyPartitionsDefinition,
    Definitions,
    IdentityPartitionMapping,
    TimeWindow,
    TimeWindowPartitionsDefinition,
    asset,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    DEFAULT_DATE_FORMAT,
    AllPartitionsSubset,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partition_mapping import LastPartitionMapping, StaticPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    PersistedTimeWindow,
    TimeWindowPartitionsSubset,
)
from dagster._core.instance import DagsterInstance
from dagster._time import create_datetime, get_current_datetime
from dagster_shared.check import CheckError


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

    assert asset_graph_view_t0._instance is instance  # noqa: SLF001

    assert asset_graph_view_t0.asset_graph.get_all_asset_keys() == {an_asset.key}


def test_upstream_non_existent_partitions():
    xy = StaticPartitionsDefinition(["x", "y"])
    zx = StaticPartitionsDefinition(["z", "x"])

    @asset(partitions_def=xy)
    def up_asset() -> None: ...

    @asset(
        deps=[AssetDep(up_asset, partition_mapping=IdentityPartitionMapping())],
        partitions_def=zx,
    )
    def down_asset(): ...

    defs = Definitions([up_asset, down_asset])

    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance)
        down_subset = asset_graph_view.get_full_subset(key=down_asset.key)
        assert down_subset.expensively_compute_partition_keys() == {"x", "z"}

        parent_subset, required_but_nonexistent_subset = (
            asset_graph_view.compute_parent_subset_and_required_but_nonexistent_subset(
                parent_key=up_asset.key, subset=down_subset
            )
        )

        assert parent_subset.expensively_compute_partition_keys() == {"x"}
        assert required_but_nonexistent_subset.expensively_compute_partition_keys() == {"z"}

        # Mapping onto an empty subset is empty
        empty_down_subset = asset_graph_view.get_empty_subset(key=down_asset.key)
        parent_subset, required_but_nonexistent_subset = (
            asset_graph_view.compute_parent_subset_and_required_but_nonexistent_subset(
                parent_key=up_asset.key, subset=empty_down_subset
            )
        )
        assert parent_subset.is_empty
        assert required_but_nonexistent_subset.is_empty


current_partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")


@asset(partitions_def=current_partitions_def)
def asset0(): ...


defs = Definitions([asset0])


def test_partitions_definition_valid_subset():
    # partition subset that is still valid because it is a subset of the current one
    old_partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")
    old_partitions_subset = TimeWindowPartitionsSubset(
        partitions_def=old_partitions_def,
        num_partitions=None,
        included_time_windows=[
            PersistedTimeWindow.from_public_time_window(
                TimeWindow(start=create_datetime(2023, 1, 1), end=create_datetime(2023, 3, 1)),
                "UTC",
            )
        ],
    )
    old_asset_graph_subset = AssetGraphSubset(
        partitions_subsets_by_asset_key={asset0.key: old_partitions_subset}
    )

    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance)

        entity_subset = asset_graph_view.get_entity_subset_from_asset_graph_subset(
            old_asset_graph_subset,
            asset0.key,
        )

        subset = cast(TimeWindowPartitionsSubset, entity_subset.get_internal_subset_value())
        assert subset.included_time_windows == old_partitions_subset.included_time_windows
        assert subset.partitions_def == current_partitions_def


@pytest.mark.parametrize(
    "invalid_asset_graph_subset, error_match",
    [
        (
            AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    asset0.key: TimeWindowPartitionsSubset(
                        partitions_def=DailyPartitionsDefinition(start_date="2021-01-01"),
                        num_partitions=None,
                        included_time_windows=[
                            PersistedTimeWindow.from_public_time_window(
                                TimeWindow(
                                    start=create_datetime(2021, 1, 1),
                                    end=create_datetime(2021, 3, 1),
                                ),
                                "UTC",
                            )
                        ],
                    )
                }
            ),
            "that are no longer present",
        ),
        (
            AssetGraphSubset(non_partitioned_asset_keys={asset0.key}),
            "was un-partitioned when originally stored, but is now partitioned.",
        ),
        (
            AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    asset0.key: TimeWindowPartitionsSubset(
                        partitions_def=DailyPartitionsDefinition(
                            start_date="2021-01-01", timezone="US/Pacific"
                        ),
                        num_partitions=None,
                        included_time_windows=[],
                    )
                }
            ),
            "is no longer compatible with the latest partitions definition",
        ),
        (
            AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    asset0.key: TimeWindowPartitionsSubset(
                        partitions_def=TimeWindowPartitionsDefinition(
                            start="2021-01-01",
                            fmt=DEFAULT_DATE_FORMAT,
                            cron_schedule="* * * * *",
                        ),
                        num_partitions=None,
                        included_time_windows=[],
                    )
                }
            ),
            "is no longer compatible with the latest partitions definition",
        ),
        (
            AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    asset0.key: TimeWindowPartitionsSubset(
                        partitions_def=TimeWindowPartitionsDefinition(
                            start="2021-01-01-UTC",
                            cron_schedule="0 0 * * *",
                            fmt="%Y-%m-%d-%Z",
                        ),
                        num_partitions=None,
                        included_time_windows=[],
                    )
                }
            ),
            "is no longer compatible with the latest partitions definition",
        ),
    ],
)
def test_partitions_definition_invalid_subset(invalid_asset_graph_subset, error_match):
    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance)

        with pytest.raises(CheckError, match=error_match):
            asset_graph_view.get_entity_subset_from_asset_graph_subset(
                invalid_asset_graph_subset,
                asset0.key,
            )


def test_all_partitions_subset_changes():
    current_partitions_def = StaticPartitionsDefinition(["FOO", "BAR"])

    @asset(partitions_def=current_partitions_def)
    def asset1(): ...

    defs = Definitions([asset1])
    effective_dt = get_current_datetime()
    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance, effective_dt)

        stored_partitions_subset = AllPartitionsSubset(
            current_partitions_def,
            dynamic_partitions_store=instance,
            current_time=asset_graph_view.effective_dt,
        )
        assert (
            asset_graph_view.get_entity_subset_from_asset_graph_subset(
                AssetGraphSubset(
                    partitions_subsets_by_asset_key={
                        asset1.key: stored_partitions_subset,
                    }
                ),
                asset1.key,
            ).get_internal_subset_value()
            == stored_partitions_subset
        )

        # fails if the underlying partitions def for an AllPartitionsSubset changes at all

        old_partitions_def = StaticPartitionsDefinition(["FOO", "BAR", "BAZ"])
        old_partitions_subset = AllPartitionsSubset(
            old_partitions_def,
            dynamic_partitions_store=instance,
            current_time=asset_graph_view.effective_dt,
        )

        with pytest.raises(
            CheckError,
            match="Partitions definition for asset1 has an AllPartitionsSubset and no longer matches the stored partitions definition",
        ):
            asset_graph_view.get_entity_subset_from_asset_graph_subset(
                AssetGraphSubset(
                    partitions_subsets_by_asset_key={
                        asset1.key: old_partitions_subset,
                    }
                ),
                asset1.key,
            )


def test_partitions_def_changes():
    static_partitions_def = StaticPartitionsDefinition(["FOO", "BAR"])

    @asset(partitions_def=static_partitions_def)
    def asset1(): ...

    @asset
    def unpartitioned_asset():
        pass

    defs = Definitions([asset1, unpartitioned_asset])
    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance)
        old_partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")
        old_partitions_subset = TimeWindowPartitionsSubset(
            partitions_def=old_partitions_def,
            num_partitions=None,
            included_time_windows=[
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(start=create_datetime(2023, 1, 1), end=create_datetime(2023, 3, 1)),
                    "UTC",
                )
            ],
        )
        # Changed to a StaticPartitionsDefinition
        with pytest.raises(
            CheckError, match="is no longer compatible with the latest partitions definition"
        ):
            asset_graph_view.get_entity_subset_from_asset_graph_subset(
                AssetGraphSubset(
                    partitions_subsets_by_asset_key={
                        asset1.key: old_partitions_subset,
                    }
                ),
                asset1.key,
            )

        # Changed to an unpartitioned asset
        with pytest.raises(
            CheckError,
            match="was partitioned when originally stored, but is no longer partitioned.",
        ):
            asset_graph_view.get_entity_subset_from_asset_graph_subset(
                AssetGraphSubset(
                    partitions_subsets_by_asset_key={
                        unpartitioned_asset.key: old_partitions_subset,
                    }
                ),
                unpartitioned_asset.key,
            )


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
        check_specs=[AssetCheckSpec("down", asset="down_letters")],
    )
    def down_letters(): ...

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
    ).expensively_compute_partition_keys() == {"a", "b", "c"}

    # from full down to up
    down_subset = asset_graph_view_t0.get_full_subset(key=down_letters.key)
    assert down_subset.expensively_compute_partition_keys() == {"a", "b", "c"}
    assert down_subset.compute_parent_subset(
        up_numbers.key
    ).expensively_compute_partition_keys() == {
        "1",
        "2",
        "3",
    }

    full_subset = asset_graph_view_t0.get_full_subset(key=down_letters.key)
    empty_subset = asset_graph_view_t0.get_empty_subset(key=down_letters.key)
    full_check_subset = asset_graph_view_t0.get_full_subset(key=down_letters.check_key)
    empty_check_subset = asset_graph_view_t0.get_empty_subset(key=down_letters.check_key)
    assert full_subset.compute_child_subset(down_letters.check_key) == full_check_subset
    assert empty_subset.compute_child_subset(down_letters.check_key) == empty_check_subset
    assert (
        full_check_subset.compute_parent_subset(
            down_letters.key
        ).expensively_compute_asset_partitions()
        == full_subset.expensively_compute_asset_partitions()
    )
    assert (
        empty_check_subset.compute_parent_subset(
            down_letters.key
        ).expensively_compute_asset_partitions()
        == empty_subset.expensively_compute_asset_partitions()
    )

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


def test_downstream_of_unpartitioned_partition_mapping() -> None:
    @asset
    def unpartitioned() -> None: ...

    @asset(
        partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
        deps=[AssetDep(unpartitioned, partition_mapping=LastPartitionMapping())],
    )
    def downstream() -> None: ...

    defs = Definitions([downstream, unpartitioned])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    unpartitioned_full = asset_graph_view.get_full_subset(key=unpartitioned.key)
    unpartitioned_empty = asset_graph_view.get_empty_subset(key=unpartitioned.key)

    downstream_full = asset_graph_view.get_full_subset(key=downstream.key)
    downstream_empty = asset_graph_view.get_empty_subset(key=downstream.key)

    assert unpartitioned_full.compute_child_subset(child_key=downstream.key) == downstream_full
    assert unpartitioned_empty.compute_child_subset(child_key=downstream.key) == downstream_empty

    assert downstream_full.compute_parent_subset(parent_key=unpartitioned.key) == unpartitioned_full
    assert (
        downstream_empty.compute_parent_subset(parent_key=unpartitioned.key) == unpartitioned_empty
    )

    assert asset_graph_view.compute_parent_subset_and_required_but_nonexistent_subset(
        parent_key=unpartitioned.key, subset=downstream_full
    ) == (unpartitioned_full, unpartitioned_empty)

    assert asset_graph_view.compute_parent_subset_and_required_but_nonexistent_subset(
        parent_key=unpartitioned.key, subset=downstream_empty
    ) == (unpartitioned_empty, unpartitioned_empty)


def test_upstream_of_unpartitioned_partition_mapping() -> None:
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
    def upstream() -> None: ...

    @asset(
        deps=[AssetDep(upstream, partition_mapping=LastPartitionMapping())],
    )
    def unpartitioned() -> None: ...

    defs = Definitions([upstream, unpartitioned])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    unpartitioned_full = asset_graph_view.get_full_subset(key=unpartitioned.key)
    unpartitioned_empty = asset_graph_view.get_empty_subset(key=unpartitioned.key)

    upstream_full = asset_graph_view.get_full_subset(key=upstream.key)
    upstream_empty = asset_graph_view.get_empty_subset(key=upstream.key)
    upstream_last = asset_graph_view.get_asset_subset_from_asset_partitions(
        key=upstream.key, asset_partitions={AssetKeyPartitionKey(upstream.key, "c")}
    )

    assert upstream_full.compute_child_subset(child_key=unpartitioned.key) == unpartitioned_full
    assert upstream_last.compute_child_subset(child_key=unpartitioned.key) == unpartitioned_full

    assert (
        unpartitioned_full.compute_parent_subset(
            parent_key=upstream.key
        ).expensively_compute_asset_partitions()
        == upstream_last.expensively_compute_asset_partitions()
    )
    assert unpartitioned_empty.compute_parent_subset(parent_key=upstream.key) == upstream_empty
