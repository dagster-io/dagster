import operator
from typing import Optional

import pytest
from dagster import (
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    deserialize_value,
    serialize_value,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, SerializableEntitySubset

partitions_defs = [
    None,
    DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
    HourlyPartitionsDefinition(start_date="2020-01-01-00:00", end_date="2020-01-02-00:00"),
    StaticPartitionsDefinition(["a", "b", "c"]),
    MultiPartitionsDefinition(
        {
            "day": DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
            "other": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    ),
]


@pytest.mark.parametrize("partitions_def", partitions_defs)
@pytest.mark.parametrize("first_all", [True, False])
@pytest.mark.parametrize("second_all", [True, False])
def test_operations(
    partitions_def: Optional[PartitionsDefinition], first_all: bool, second_all: bool
) -> None:
    @asset(partitions_def=partitions_def)
    def foo() -> None: ...

    defs = Definitions([foo])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    a = (
        asset_graph_view.get_full_subset(key=foo.key)
        if first_all
        else asset_graph_view.get_empty_subset(key=foo.key)
    )
    b = (
        asset_graph_view.get_full_subset(key=foo.key)
        if second_all
        else asset_graph_view.get_empty_subset(key=foo.key)
    )

    def _assert_matches_operation(res, oper):
        expected_aps = oper(
            a.expensively_compute_asset_partitions(), b.expensively_compute_asset_partitions()
        )
        actual_aps = res.expensively_compute_asset_partitions()
        assert expected_aps == actual_aps, oper

    or_res = a.compute_union(b)
    _assert_matches_operation(or_res, operator.or_)
    and_res = a.compute_intersection(b)
    _assert_matches_operation(and_res, operator.and_)
    sub_res = a.compute_difference(b)
    _assert_matches_operation(sub_res, operator.sub)


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_round_trip(partitions_def: Optional[PartitionsDefinition]) -> None:
    @asset(partitions_def=partitions_def)
    def foo() -> None: ...

    defs = Definitions([foo])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    initial_subset = asset_graph_view.get_full_subset(key=foo.key)

    inner_subset = deserialize_value(
        serialize_value(initial_subset.convert_to_serializable_subset()), SerializableEntitySubset
    )
    subset = asset_graph_view.get_subset_from_serializable_subset(inner_subset)

    assert subset is not None
    assert (
        initial_subset.expensively_compute_asset_partitions()
        == subset.expensively_compute_asset_partitions()
    )

    # if asset is removed, don't error just return None
    empty_asset_graph_view = AssetGraphView.for_test(Definitions(), instance)
    subset = empty_asset_graph_view.get_subset_from_serializable_subset(inner_subset)
    assert subset is None
