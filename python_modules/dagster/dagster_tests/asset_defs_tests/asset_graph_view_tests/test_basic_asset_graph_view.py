from typing import cast

import dagster as dg
import pytest
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.subset import (
    AllPartitionsSubset,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.partitions.utils import PersistedTimeWindow
from dagster._core.instance import DagsterInstance
from dagster._time import create_datetime
from dagster._utils.partitions import DEFAULT_DATE_FORMAT
from dagster_shared.check import CheckError


def test_basic_construction_and_identity() -> None:
    @dg.asset
    def an_asset() -> None: ...

    defs = dg.Definitions([an_asset])
    instance = DagsterInstance.ephemeral()
    effective_dt = create_datetime(2020, 1, 1)
    last_event_id = 928348343
    asset_graph_view_t0 = AssetGraphView.for_test(defs, instance, effective_dt, last_event_id)

    assert asset_graph_view_t0
    assert asset_graph_view_t0.effective_dt == effective_dt
    assert asset_graph_view_t0.last_event_id == last_event_id

    assert asset_graph_view_t0._instance is instance  # noqa: SLF001

    assert asset_graph_view_t0.asset_graph.get_all_asset_keys() == {an_asset.key}


def test_not_in_graph_partitions():
    xy = dg.StaticPartitionsDefinition(["x", "y"])
    dynamic = dg.DynamicPartitionsDefinition(name="dynamic_partition")

    @dg.asset(partitions_def=xy)
    def the_asset() -> None: ...

    @dg.asset(partitions_def=dynamic)
    def the_dynamic_asset() -> None: ...

    defs = dg.Definitions([the_asset, the_dynamic_asset])

    with DagsterInstance.ephemeral() as instance:
        instance.add_dynamic_partitions("dynamic_partition", ["a", "b", "c"])
        asset_graph_view = AssetGraphView.for_test(defs, instance)

        candidate_subset = asset_graph_view.get_asset_subset_from_asset_partitions(
            key=the_asset.key,
            asset_partitions={
                AssetKeyPartitionKey(the_asset.key, "x"),
                AssetKeyPartitionKey(the_asset.key, "a"),
                AssetKeyPartitionKey(the_asset.key, "b"),
            },
        )

        assert asset_graph_view.get_subset_not_in_graph(
            key=the_asset.key, candidate_subset=candidate_subset
        ).expensively_compute_partition_keys() == {"a", "b"}

        dynamic_candidate_subset = asset_graph_view.get_asset_subset_from_asset_partitions(
            key=the_dynamic_asset.key,
            asset_partitions={
                AssetKeyPartitionKey(the_dynamic_asset.key, "c"),
                AssetKeyPartitionKey(the_dynamic_asset.key, "d"),
                AssetKeyPartitionKey(the_dynamic_asset.key, "e"),
            },
        )

        assert asset_graph_view.get_subset_not_in_graph(
            key=the_dynamic_asset.key, candidate_subset=dynamic_candidate_subset
        ).expensively_compute_partition_keys() == {"d", "e"}


def test_upstream_non_existent_partitions():
    xy = dg.StaticPartitionsDefinition(["x", "y"])
    zx = dg.StaticPartitionsDefinition(["z", "x"])

    @dg.asset(partitions_def=xy)
    def up_asset() -> None: ...

    @dg.asset(
        deps=[dg.AssetDep(up_asset, partition_mapping=dg.IdentityPartitionMapping())],
        partitions_def=zx,
    )
    def down_asset(): ...

    defs = dg.Definitions([up_asset, down_asset])

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


current_partitions_def = dg.DailyPartitionsDefinition(start_date="2022-01-01")


@dg.asset(partitions_def=current_partitions_def)
def asset0(): ...


defs = dg.Definitions([asset0])


def test_partitions_definition_valid_subset():
    # partition subset that is still valid because it is a subset of the current one
    old_partitions_def = dg.DailyPartitionsDefinition(start_date="2023-01-01")
    old_partitions_subset = TimeWindowPartitionsSubset(
        partitions_def=old_partitions_def,
        num_partitions=None,
        included_time_windows=[
            PersistedTimeWindow.from_public_time_window(
                dg.TimeWindow(start=create_datetime(2023, 1, 1), end=create_datetime(2023, 3, 1)),
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

        subset = cast("TimeWindowPartitionsSubset", entity_subset.get_internal_subset_value())
        assert subset.included_time_windows == old_partitions_subset.included_time_windows
        assert subset.partitions_def == current_partitions_def

        new_asset_graph_subset = (
            asset_graph_view.get_latest_asset_graph_subset_from_serialized_asset_graph_subset(
                old_asset_graph_subset
            )
        )

        assert (
            new_asset_graph_subset != old_asset_graph_subset
        )  # because the partitions defs are different

        assert new_asset_graph_subset.partitions_subsets_by_asset_key[asset0.key] == subset


@pytest.mark.parametrize(
    "invalid_asset_graph_subset, error_match",
    [
        (
            AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    asset0.key: TimeWindowPartitionsSubset(
                        partitions_def=dg.DailyPartitionsDefinition(start_date="2021-01-01"),
                        num_partitions=None,
                        included_time_windows=[
                            PersistedTimeWindow.from_public_time_window(
                                dg.TimeWindow(
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
                        partitions_def=dg.DailyPartitionsDefinition(
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
                        partitions_def=dg.TimeWindowPartitionsDefinition(
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
                        partitions_def=dg.TimeWindowPartitionsDefinition(
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
    current_partitions_def = dg.StaticPartitionsDefinition(["FOO", "BAR"])

    @dg.asset(partitions_def=current_partitions_def)
    def asset1(): ...

    defs = dg.Definitions([asset1])
    with DagsterInstance.ephemeral() as instance, partition_loading_context(None, instance) as ctx:
        asset_graph_view = AssetGraphView.for_test(defs, instance, ctx.effective_dt)

        stored_partitions_subset = AllPartitionsSubset(current_partitions_def, ctx)
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

        old_partitions_def = dg.StaticPartitionsDefinition(["FOO", "BAR", "BAZ"])
        old_partitions_subset = AllPartitionsSubset(old_partitions_def, ctx)

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
    static_partitions_def = dg.StaticPartitionsDefinition(["FOO", "BAR"])

    @dg.asset(partitions_def=static_partitions_def)
    def asset1(): ...

    @dg.asset
    def unpartitioned_asset():
        pass

    defs = dg.Definitions([asset1, unpartitioned_asset])
    with DagsterInstance.ephemeral() as instance:
        asset_graph_view = AssetGraphView.for_test(defs, instance)
        old_partitions_def = dg.DailyPartitionsDefinition(start_date="2023-01-01")
        old_partitions_subset = TimeWindowPartitionsSubset(
            partitions_def=old_partitions_def,
            num_partitions=None,
            included_time_windows=[
                PersistedTimeWindow.from_public_time_window(
                    dg.TimeWindow(
                        start=create_datetime(2023, 1, 1), end=create_datetime(2023, 3, 1)
                    ),
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
    number_static_partitions_def = dg.StaticPartitionsDefinition(list(number_keys))
    letter_static_partitions_def = dg.StaticPartitionsDefinition(list(letter_keys))
    mapping = dg.StaticPartitionMapping({"1": "a", "2": "b", "3": "c"})

    @dg.asset(partitions_def=number_static_partitions_def)
    def up_numbers() -> None: ...

    @dg.asset(
        deps=[dg.AssetDep(up_numbers, partition_mapping=mapping)],
        partitions_def=letter_static_partitions_def,
        check_specs=[dg.AssetCheckSpec("down", asset="down_letters")],
    )
    def down_letters(): ...

    defs = dg.Definitions([up_numbers, down_letters])
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
    number_static_partitions_def = dg.StaticPartitionsDefinition(list(number_keys))

    @dg.asset(partitions_def=number_static_partitions_def)
    def up_numbers() -> None: ...

    defs = dg.Definitions([up_numbers])
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
    @dg.asset
    def unpartitioned() -> None: ...

    @dg.asset(
        partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
        deps=[dg.AssetDep(unpartitioned, partition_mapping=dg.LastPartitionMapping())],
    )
    def downstream() -> None: ...

    defs = dg.Definitions([downstream, unpartitioned])
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
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
    def upstream() -> None: ...

    @dg.asset(
        deps=[dg.AssetDep(upstream, partition_mapping=dg.LastPartitionMapping())],
    )
    def unpartitioned() -> None: ...

    defs = dg.Definitions([upstream, unpartitioned])
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
