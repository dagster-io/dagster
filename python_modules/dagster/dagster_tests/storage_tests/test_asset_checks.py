import dagster as dg
import pytest
from dagster import DagsterInstance


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


@dg.asset
def the_asset():
    return 1


@dg.asset_check(asset=the_asset)
def the_asset_check():
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(assets=[the_asset], asset_checks=[the_asset_check])


def test_get_asset_check_summary_records(instance: DagsterInstance):
    records = instance.event_log_storage.get_asset_check_summary_records(
        asset_check_keys=list(the_asset_check.check_keys)
    )
    assert len(records) == 1
    check_key = the_asset_check.check_key
    summary_record = records[check_key]
    assert summary_record.asset_check_key == next(iter(the_asset_check.check_keys))
    assert summary_record.last_check_execution_record is None
    assert summary_record.last_run_id is None
    implicit_job = defs.resolve_all_job_defs()[0]
    result = implicit_job.execute_in_process(instance=instance)
    assert result.success
    records = instance.event_log_storage.get_asset_check_summary_records(
        asset_check_keys=list(the_asset_check.check_keys)
    )
    assert len(records) == 1
    assert records[check_key].last_check_execution_record.event.asset_check_evaluation.passed  # type: ignore
    assert records[check_key].last_run_id == result.run_id


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
def partitioned_asset(context):
    return f"data_for_{context.partition_key}"


@dg.asset_check(
    asset=partitioned_asset, partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"])
)
def partitioned_asset_check(context):
    # Simulate different outcomes for different partitions
    if context.partition_key == "a":
        return dg.AssetCheckResult(passed=True, description="Partition a passed")
    elif context.partition_key == "b":
        return dg.AssetCheckResult(passed=False, description="Partition b failed")
    else:
        # Partition c will be planned but not executed in tests
        return dg.AssetCheckResult(passed=True, description="Partition c passed")


partitioned_defs = dg.Definitions(
    assets=[partitioned_asset], asset_checks=[partitioned_asset_check]
)


def test_partitioned_asset_check_graph_structure():
    """Test basic graph structure for partitioned asset checks."""
    from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
    from dagster._core.definitions.assets.graph.base_asset_graph import AssetCheckNode

    asset_graph = AssetGraph.from_assets([partitioned_asset, partitioned_asset_check])

    # Test: asset check node exists and is correctly configured
    check_node = asset_graph.get(partitioned_asset_check.check_key)
    assert isinstance(check_node, AssetCheckNode)
    assert check_node.partitions_def is not None
    assert check_node.partitions_def.get_partition_keys() == ["a", "b", "c"]

    # Test: check is linked to asset
    asset_node = asset_graph.get(partitioned_asset.key)
    assert partitioned_asset_check.check_key in asset_node.check_keys


@pytest.mark.asyncio
async def test_partitioned_asset_check_subset_computation_empty():
    """Test subset computation for partitioned asset checks before any executions."""
    from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus

    with dg.instance_for_test() as instance:
        view = AssetGraphView.for_test(partitioned_defs, instance=instance)
        partitioned_key = partitioned_asset_check.check_key

        # Before executions, all partitions should be missing
        missing_subset = await view.compute_subset_with_status(partitioned_key, None)
        assert not missing_subset.is_empty
        assert missing_subset.expensively_compute_partition_keys() == {"a", "b", "c"}

        # No partitions should have execution statuses
        for status in [
            AssetCheckExecutionResolvedStatus.SUCCEEDED,
            AssetCheckExecutionResolvedStatus.FAILED,
            AssetCheckExecutionResolvedStatus.IN_PROGRESS,
        ]:
            subset = await view.compute_subset_with_status(partitioned_key, status)
            assert subset.is_empty


@pytest.mark.asyncio
async def test_partitioned_asset_check_subset_computation_after_execution():
    """Test subset computation after executing partitions with different outcomes."""
    from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus

    with dg.instance_for_test() as instance:
        # Execute partitions with known outcomes
        result_a = dg.materialize(
            [partitioned_asset, partitioned_asset_check], instance=instance, partition_key="a"
        )
        assert result_a.success

        result_b = dg.materialize(
            [partitioned_asset, partitioned_asset_check], instance=instance, partition_key="b"
        )
        assert result_b.success  # Run succeeds but check fails

        view = AssetGraphView.for_test(partitioned_defs, instance=instance)
        partitioned_key = partitioned_asset_check.check_key

        # Test: subsets reflect execution outcomes
        succeeded_subset = await view.compute_subset_with_status(
            partitioned_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert not succeeded_subset.is_empty
        assert succeeded_subset.expensively_compute_partition_keys() == {"a"}

        failed_subset = await view.compute_subset_with_status(
            partitioned_key, AssetCheckExecutionResolvedStatus.FAILED
        )
        assert not failed_subset.is_empty  # Should contain 'b'
        assert failed_subset.expensively_compute_partition_keys() == {"b"}

        missing_subset = await view.compute_subset_with_status(partitioned_key, None)
        assert not missing_subset.is_empty  # Should contain 'c'
        assert missing_subset.expensively_compute_partition_keys() == {"c"}


@pytest.mark.asyncio
async def test_non_partitioned_asset_check_compatibility():
    """Test that non-partitioned asset checks still work with existing logic."""
    from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus

    with dg.instance_for_test() as instance:
        view = AssetGraphView.for_test(defs, instance=instance)
        non_partitioned_key = the_asset_check.check_key

        missing_subset = await view.compute_subset_with_status(non_partitioned_key, None)
        assert not missing_subset.is_partitioned

        succeeded_subset = await view.compute_subset_with_status(
            non_partitioned_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert not succeeded_subset.is_partitioned

        # Execute the check
        result = dg.materialize([the_asset, the_asset_check], instance=instance)
        assert result.success

        # After execution
        view_after = AssetGraphView.for_test(defs, instance=instance)
        succeeded_subset_after = await view_after.compute_subset_with_status(
            non_partitioned_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert not succeeded_subset_after.is_partitioned
