import asyncio
from typing import Optional

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.events import StepMaterializationData
from dagster._core.events.log import DagsterEventType
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test


def create_check_planned_event(
    run_id: str,
    check_key: dg.AssetCheckKey,
    partitions_subset: Optional[PartitionsSubset] = None,
    timestamp: float = 0.0,
) -> dg.EventLogEntry:
    """Helper to create an ASSET_CHECK_EVALUATION_PLANNED event."""
    return dg.EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
            "nonce",
            event_specific_data=AssetCheckEvaluationPlanned(
                asset_key=check_key.asset_key,
                check_name=check_key.name,
                partitions_subset=partitions_subset.to_serializable_subset()
                if partitions_subset
                else None,
            ),
        ),
    )


def create_check_evaluation_event(
    run_id: str,
    check_key: dg.AssetCheckKey,
    passed: bool,
    partition: Optional[str] = None,
    target_materialization_data: Optional[AssetCheckEvaluationTargetMaterializationData] = None,
    timestamp: float = 0.0,
) -> dg.EventLogEntry:
    """Helper to create an ASSET_CHECK_EVALUATION event."""
    return dg.EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            DagsterEventType.ASSET_CHECK_EVALUATION.value,
            "nonce",
            event_specific_data=AssetCheckEvaluation(
                asset_key=check_key.asset_key,
                check_name=check_key.name,
                passed=passed,
                metadata={},
                target_materialization_data=target_materialization_data,
                severity=dg.AssetCheckSeverity.ERROR,
                partition=partition,
            ),
        ),
    )


def create_materialization_event(
    run_id: str,
    asset_key: dg.AssetKey,
    partition: Optional[str] = None,
    timestamp: float = 0.0,
) -> dg.EventLogEntry:
    """Helper to create an ASSET_MATERIALIZATION event."""
    return dg.EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            DagsterEventType.ASSET_MATERIALIZATION.value,
            "nonce",
            event_specific_data=StepMaterializationData(
                materialization=dg.AssetMaterialization(
                    asset_key=asset_key,
                    partition=partition,
                ),
                asset_lineage=[],
            ),
        ),
    )


def create_run_success_event(run_id: str, timestamp: float = 0.0) -> dg.EventLogEntry:
    """Helper to create a PIPELINE_SUCCESS event."""
    return dg.EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            DagsterEventType.PIPELINE_SUCCESS.value,
            "nonce",
        ),
    )


def create_partitioned_asset_with_check(partitions_def: dg.PartitionsDefinition):
    """Create a partitioned asset with an associated asset check."""

    @dg.asset(partitions_def=partitions_def)
    def test_asset():
        return 1

    @dg.asset_check(asset=test_asset, partitions_def=partitions_def)
    def test_check():
        return dg.AssetCheckResult(passed=True)

    return test_asset, test_check


def get_partition_keys_for_def(
    partitions_def: dg.PartitionsDefinition, instance: DagsterInstance
) -> list[str]:
    """Get partition keys for any partition definition type."""
    if isinstance(partitions_def, dg.DynamicPartitionsDefinition):
        return list(partitions_def.get_partition_keys(dynamic_partitions_store=instance))
    elif isinstance(partitions_def, dg.MultiPartitionsDefinition):
        # For multi partitions, get all combinations
        keys = []
        for pk in partitions_def.get_partition_keys():
            keys.append(str(pk))
        return keys
    else:
        return list(partitions_def.get_partition_keys())


async def get_status_subset(
    asset_graph_view: AssetGraphView,
    check_key: dg.AssetCheckKey,
    status: Optional[AssetCheckExecutionResolvedStatus],
):
    """Helper to get partition keys with given status."""
    full_subset = asset_graph_view.get_full_subset(key=check_key)
    result_subset = await asset_graph_view.compute_subset_with_status(
        check_key, status, full_subset
    )
    return result_subset.expensively_compute_partition_keys()


def get_materialization_storage_id(
    instance: DagsterInstance, asset_key: dg.AssetKey, partition: str
) -> tuple[int, float]:
    """Get the storage_id and timestamp of the latest materialization for a partition."""
    records = instance.event_log_storage.get_event_records(
        dg.EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
            asset_partitions=[partition],
        ),
        limit=1,
        ascending=False,
    )
    return records[0].storage_id, records[0].timestamp


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


STATIC_PARTITIONS_DEF = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])
DAILY_PARTITIONS_DEF = dg.DailyPartitionsDefinition(start_date="2026-01-01")
MULTI_PARTITIONS_DEF = dg.MultiPartitionsDefinition(
    {
        "dim1": dg.StaticPartitionsDefinition(["x", "y"]),
        "dim2": dg.StaticPartitionsDefinition(["1", "2"]),
    }
)
DYNAMIC_PARTITIONS_DEF = dg.DynamicPartitionsDefinition(name="dynamic_test")


@pytest.fixture(
    params=[
        pytest.param(STATIC_PARTITIONS_DEF, id="static"),
        pytest.param(DAILY_PARTITIONS_DEF, id="daily"),
        pytest.param(MULTI_PARTITIONS_DEF, id="multi"),
        pytest.param(DYNAMIC_PARTITIONS_DEF, id="dynamic"),
    ]
)
def partitions_def(request, instance: DagsterInstance):
    """Fixture that provides different partition definition types."""
    partitions_def = request.param
    # For dynamic partitions, we need to register the partitions first
    if isinstance(partitions_def, dg.DynamicPartitionsDefinition):
        # Use the known name directly to satisfy type checker
        instance.add_dynamic_partitions("dynamic_test", ["p1", "p2", "p3", "p4"])
    return partitions_def


# --- Tests ---


def test_partitioned_check_status_lifecycle(
    instance: DagsterInstance, partitions_def: dg.PartitionsDefinition
):
    """Test complete lifecycle: None -> IN_PROGRESS -> SUCCEEDED/FAILED.

    This test covers:
    - Initially all partitions are None (missing)
    - Planning a check makes it IN_PROGRESS
    - Completing a check successfully makes it SUCCEEDED
    - Failing a check explicitly makes it FAILED
    """
    test_asset, test_check = create_partitioned_asset_with_check(partitions_def)
    defs = dg.Definitions(assets=[test_asset], asset_checks=[test_check])

    asset_key = test_asset.key
    check_key = test_check.check_key

    # Get partition keys for this partition definition
    all_partition_keys = get_partition_keys_for_def(partitions_def, instance)
    assert len(all_partition_keys) >= 4, "Need at least 4 partitions for this test"

    # Pick specific partitions for different statuses
    partition_to_succeed = all_partition_keys[0]
    partition_to_fail = all_partition_keys[1]
    partition_in_progress = all_partition_keys[2]
    partition_missing = all_partition_keys[3]

    async def run_test():
        # Create initial view - all should be None (missing)
        view = AssetGraphView.for_test(defs, instance)
        assert await get_status_subset(view, check_key, None) == set(all_partition_keys)
        assert (
            await get_status_subset(view, check_key, AssetCheckExecutionResolvedStatus.SUCCEEDED)
            == set()
        )
        assert (
            await get_status_subset(view, check_key, AssetCheckExecutionResolvedStatus.FAILED)
            == set()
        )
        assert (
            await get_status_subset(view, check_key, AssetCheckExecutionResolvedStatus.IN_PROGRESS)
            == set()
        )

        # Materialize partitions first (checks need to target a materialization)
        run_mat = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        ts = 1.0
        for pk in [partition_to_succeed, partition_to_fail, partition_in_progress]:
            instance.event_log_storage.store_event(
                create_materialization_event(run_mat.run_id, asset_key, partition=pk, timestamp=ts)
            )
            ts += 1.0
        instance.handle_new_event(create_run_success_event(run_mat.run_id, timestamp=ts))

        # Run 1: Check stays IN_PROGRESS (run still STARTED)
        run_in_progress = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run_in_progress.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys(
                    [partition_in_progress]
                ),
                timestamp=10.0,
            )
        )

        # Run 2: Check completes successfully
        run_success = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        storage_id, mat_ts = get_materialization_storage_id(
            instance, asset_key, partition_to_succeed
        )
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run_success.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys([partition_to_succeed]),
                timestamp=20.0,
            )
        )
        instance.event_log_storage.store_event(
            create_check_evaluation_event(
                run_success.run_id,
                check_key,
                passed=True,
                partition=partition_to_succeed,
                target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                    storage_id=storage_id,
                    run_id=run_mat.run_id,
                    timestamp=mat_ts,
                ),
                timestamp=21.0,
            )
        )
        instance.handle_new_event(create_run_success_event(run_success.run_id, timestamp=22.0))

        # Run 3: Check explicitly fails
        run_failed_check = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        storage_id, mat_ts = get_materialization_storage_id(instance, asset_key, partition_to_fail)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run_failed_check.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys([partition_to_fail]),
                timestamp=30.0,
            )
        )
        instance.event_log_storage.store_event(
            create_check_evaluation_event(
                run_failed_check.run_id,
                check_key,
                passed=False,
                partition=partition_to_fail,
                target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                    storage_id=storage_id,
                    run_id=run_mat.run_id,
                    timestamp=mat_ts,
                ),
                timestamp=31.0,
            )
        )
        instance.handle_new_event(create_run_success_event(run_failed_check.run_id, timestamp=32.0))

        # Verify all statuses
        view = AssetGraphView.for_test(defs, instance)

        # Partitions that were never touched should be None
        missing_subset = await get_status_subset(view, check_key, None)
        assert partition_missing in missing_subset

        # IN_PROGRESS partition
        in_progress_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.IN_PROGRESS
        )
        assert in_progress_subset == {partition_in_progress}

        # SUCCEEDED partition
        succeeded_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert succeeded_subset == {partition_to_succeed}

        # FAILED partition
        failed_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.FAILED
        )
        assert failed_subset == {partition_to_fail}

    asyncio.run(run_test())


def test_partitioned_check_execution_failed_and_skipped(
    instance: DagsterInstance, partitions_def: dg.PartitionsDefinition
):
    """Test EXECUTION_FAILED and SKIPPED statuses.

    This test covers:
    - EXECUTION_FAILED: run fails before check completes
    - SKIPPED: run succeeds but check was never evaluated
    """
    test_asset, test_check = create_partitioned_asset_with_check(partitions_def)
    defs = dg.Definitions(assets=[test_asset], asset_checks=[test_check])

    asset_key = test_asset.key
    check_key = test_check.check_key

    all_partition_keys = get_partition_keys_for_def(partitions_def, instance)
    assert len(all_partition_keys) >= 2, "Need at least 2 partitions for this test"

    partition_exec_failed = all_partition_keys[0]
    partition_skipped = all_partition_keys[1]

    async def run_test():
        # Materialize partitions first
        run_mat = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_materialization_event(
                run_mat.run_id, asset_key, partition=partition_exec_failed, timestamp=1.0
            )
        )
        instance.event_log_storage.store_event(
            create_materialization_event(
                run_mat.run_id, asset_key, partition=partition_skipped, timestamp=2.0
            )
        )
        instance.handle_new_event(create_run_success_event(run_mat.run_id, timestamp=3.0))

        # Run 1: Plan check then fail the run -> EXECUTION_FAILED
        run_failed = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run_failed.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys(
                    [partition_exec_failed]
                ),
                timestamp=10.0,
            )
        )
        instance.report_run_failed(run_failed)

        # Run 2: Plan check then succeed run without evaluation -> SKIPPED
        run_skipped = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run_skipped.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys([partition_skipped]),
                timestamp=20.0,
            )
        )
        instance.handle_new_event(create_run_success_event(run_skipped.run_id, timestamp=21.0))

        # Verify statuses
        view = AssetGraphView.for_test(defs, instance)

        exec_failed_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
        )
        assert exec_failed_subset == {partition_exec_failed}

        skipped_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.SKIPPED
        )
        assert skipped_subset == {partition_skipped}

    asyncio.run(run_test())


def test_partitioned_check_targets_latest_materialization(
    instance: DagsterInstance, partitions_def: dg.PartitionsDefinition
):
    """Test that check status respects materialization targeting.

    This test covers:
    - Check targeting latest materialization returns SUCCEEDED
    - After re-materializing, check becomes stale (returns None)
    - New check execution returns SUCCEEDED again
    """
    test_asset, test_check = create_partitioned_asset_with_check(partitions_def)
    defs = dg.Definitions(assets=[test_asset], asset_checks=[test_check])

    asset_key = test_asset.key
    check_key = test_check.check_key

    all_partition_keys = get_partition_keys_for_def(partitions_def, instance)
    partition = all_partition_keys[0]

    async def run_test():
        # Initial materialization
        run1 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_materialization_event(run1.run_id, asset_key, partition=partition, timestamp=1.0)
        )
        instance.handle_new_event(create_run_success_event(run1.run_id, timestamp=2.0))

        storage_id1, mat_ts1 = get_materialization_storage_id(instance, asset_key, partition)

        # Execute check targeting the materialization
        run2 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run2.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys([partition]),
                timestamp=10.0,
            )
        )
        instance.event_log_storage.store_event(
            create_check_evaluation_event(
                run2.run_id,
                check_key,
                passed=True,
                partition=partition,
                target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                    storage_id=storage_id1,
                    run_id=run1.run_id,
                    timestamp=mat_ts1,
                ),
                timestamp=11.0,
            )
        )
        instance.handle_new_event(create_run_success_event(run2.run_id, timestamp=12.0))

        # Verify check is SUCCEEDED
        view = AssetGraphView.for_test(defs, instance)
        succeeded_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert partition in succeeded_subset

        # Re-materialize the partition (makes the check stale)
        run3 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_materialization_event(
                run3.run_id, asset_key, partition=partition, timestamp=20.0
            )
        )
        instance.handle_new_event(create_run_success_event(run3.run_id, timestamp=21.0))

        # Verify check is now None (stale - doesn't target latest materialization)
        view = AssetGraphView.for_test(defs, instance)
        missing_subset = await get_status_subset(view, check_key, None)
        assert partition in missing_subset

        succeeded_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert partition not in succeeded_subset

        # Execute new check targeting the new materialization
        storage_id2, mat_ts2 = get_materialization_storage_id(instance, asset_key, partition)

        run4 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        instance.event_log_storage.store_event(
            create_check_planned_event(
                run4.run_id,
                check_key,
                partitions_subset=partitions_def.subset_with_partition_keys([partition]),
                timestamp=30.0,
            )
        )
        instance.event_log_storage.store_event(
            create_check_evaluation_event(
                run4.run_id,
                check_key,
                passed=True,
                partition=partition,
                target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                    storage_id=storage_id2,
                    run_id=run3.run_id,
                    timestamp=mat_ts2,
                ),
                timestamp=31.0,
            )
        )
        instance.handle_new_event(create_run_success_event(run4.run_id, timestamp=32.0))

        # Verify check is SUCCEEDED again
        view = AssetGraphView.for_test(defs, instance)
        succeeded_subset = await get_status_subset(
            view, check_key, AssetCheckExecutionResolvedStatus.SUCCEEDED
        )
        assert partition in succeeded_subset

    asyncio.run(run_test())
