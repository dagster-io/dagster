import operator

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetJobKey

partitions_defs = [
    None,
    dg.DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
    dg.HourlyPartitionsDefinition(start_date="2020-01-01-00:00", end_date="2020-01-02-00:00"),
    dg.StaticPartitionsDefinition(["a", "b", "c"]),
    dg.MultiPartitionsDefinition(
        {
            "day": dg.DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
            "other": dg.StaticPartitionsDefinition(["a", "b", "c"]),
        }
    ),
]


@pytest.mark.parametrize("partitions_def", partitions_defs)
@pytest.mark.parametrize("first_all", [True, False])
@pytest.mark.parametrize("second_all", [True, False])
def test_operations(
    partitions_def: dg.PartitionsDefinition | None, first_all: bool, second_all: bool
) -> None:
    @dg.asset(partitions_def=partitions_def)
    def foo() -> None: ...

    defs = dg.Definitions([foo])
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
def test_round_trip(partitions_def: dg.PartitionsDefinition | None) -> None:
    @dg.asset(partitions_def=partitions_def)
    def foo() -> None: ...

    defs = dg.Definitions([foo])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    initial_subset = asset_graph_view.get_full_subset(key=foo.key)

    inner_subset = dg.deserialize_value(
        dg.serialize_value(initial_subset.convert_to_serializable_subset()),
        SerializableEntitySubset,
    )
    subset = asset_graph_view.get_subset_from_serializable_subset(inner_subset)

    assert subset is not None
    assert (
        initial_subset.expensively_compute_asset_partitions()
        == subset.expensively_compute_asset_partitions()
    )

    # if asset is removed, don't error just return None
    empty_asset_graph_view = AssetGraphView.for_test(dg.Definitions(), instance)
    subset = empty_asset_graph_view.get_subset_from_serializable_subset(inner_subset)
    assert subset is None


def test_job_key_absent_from_graph_returns_none() -> None:
    @dg.asset
    def foo() -> None: ...

    defs = dg.Definitions([foo])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    # a persisted subset may reference a key that no longer exists in the graph (e.g. a
    # job-keyed subset written by a newer version before a rollback, or a since-deleted
    # job); it is dropped rather than raising
    job_subset = SerializableEntitySubset(key=AssetJobKey("gone"), value=True)
    assert asset_graph_view.get_subset_from_serializable_subset(job_subset) is None


def test_job_key_present_in_graph_round_trips() -> None:
    @dg.asset
    def foo() -> None: ...

    job = dg.define_asset_job(
        "my_job",
        selection=[foo],
        automation_condition=dg.AutomationCondition.all_job_root_assets_match(
            dg.AutomationCondition.missing()
        ),
    )
    defs = dg.Definitions(assets=[foo], jobs=[job])
    instance = DagsterInstance.ephemeral()
    asset_graph_view = AssetGraphView.for_test(defs, instance)

    job_key = AssetJobKey("my_job")
    # a job is unpartitioned in v1, so a boolean-valued subset
    serialized = dg.deserialize_value(
        dg.serialize_value(SerializableEntitySubset(key=job_key, value=True)),
        SerializableEntitySubset,
    )
    subset = asset_graph_view.get_subset_from_serializable_subset(serialized)
    assert subset is not None
    assert subset.key == job_key
    assert not subset.is_empty
