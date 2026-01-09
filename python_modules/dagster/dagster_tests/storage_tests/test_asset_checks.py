import asyncio
from typing import Optional

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.events import StepMaterializationData
from dagster._core.events.log import DagsterEventType
from dagster._core.loader import LoadingContextForTest
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test


def _create_check_planned_event(
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
                partitions_subset=partitions_subset,
            ),
        ),
    )


def _create_check_evaluation_event(
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


def _create_materialization_event(
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


def _create_run_success_event(run_id: str, timestamp: float = 0.0) -> dg.EventLogEntry:
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


def test_resolve_status_transitions(instance: DagsterInstance):
    """Test that resolve_status() correctly resolves PLANNED checks based on run state."""
    check_key = dg.AssetCheckKey(dg.AssetKey("foo"), "bar")
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c"])
    loading_context = LoadingContextForTest(instance)

    # Run A: stays in progress (STARTED status)
    run_a = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_check_planned_event(
            run_a.run_id,
            check_key,
            partitions_subset=partitions_def.subset_with_partition_keys(["a"]),
            timestamp=1.0,
        )
    )

    # Run B: fails
    run_b = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_check_planned_event(
            run_b.run_id,
            check_key,
            partitions_subset=partitions_def.subset_with_partition_keys(["b"]),
            timestamp=2.0,
        )
    )
    instance.report_run_failed(run_b)

    # Run C: succeeds without check evaluation (check was skipped)
    run_c = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_check_planned_event(
            run_c.run_id,
            check_key,
            partitions_subset=partitions_def.subset_with_partition_keys(["c"]),
            timestamp=3.0,
        )
    )
    instance.handle_new_event(_create_run_success_event(run_c.run_id, timestamp=4.0))

    # Get the check records and verify resolve_status
    record_a = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="a"
    )[check_key]
    record_b = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="b"
    )[check_key]
    record_c = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="c"
    )[check_key]

    # Verify resolved statuses - all in one async function to avoid event loop issues
    async def verify_statuses():
        assert (
            await record_a.resolve_status(loading_context)
            == AssetCheckExecutionResolvedStatus.IN_PROGRESS
        )
        assert (
            await record_b.resolve_status(loading_context)
            == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
        )
        assert (
            await record_c.resolve_status(loading_context)
            == AssetCheckExecutionResolvedStatus.SKIPPED
        )

    asyncio.run(verify_statuses())


def test_targets_latest_materialization_scenarios(instance: DagsterInstance):
    """Test targets_latest_materialization() for partition isolation and staleness detection."""
    asset_key = dg.AssetKey("foo")
    check_key = dg.AssetCheckKey(asset_key, "bar")
    partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    # Materialize partition "a" (M1)
    run_1 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_materialization_event(run_1.run_id, asset_key, partition="a", timestamp=1.0)
    )

    # Get M1's storage_id
    mat_records = instance.event_log_storage.get_event_records(
        dg.EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
        ),
        limit=1,
        ascending=False,
    )
    m1_storage_id = mat_records[0].storage_id
    m1_timestamp = mat_records[0].timestamp

    # Execute check for partition "a" (captures target_materialization_data pointing to M1)
    instance.event_log_storage.store_event(
        _create_check_planned_event(
            run_1.run_id,
            check_key,
            partitions_subset=partitions_def.subset_with_partition_keys(["a"]),
            timestamp=2.0,
        )
    )
    instance.event_log_storage.store_event(
        _create_check_evaluation_event(
            run_1.run_id,
            check_key,
            passed=True,
            partition="a",
            target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                storage_id=m1_storage_id,
                run_id=run_1.run_id,
                timestamp=m1_timestamp,
            ),
            timestamp=3.0,
        )
    )
    instance.handle_new_event(_create_run_success_event(run_1.run_id, timestamp=4.0))

    # Verify targets_latest_materialization() returns True
    record_a = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="a"
    )[check_key]
    ctx_1 = LoadingContextForTest(instance)
    assert asyncio.run(record_a.targets_latest_materialization(ctx_1)) is True

    # Materialize partition "b" (M2) - different partition
    run_2 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_materialization_event(run_2.run_id, asset_key, partition="b", timestamp=5.0)
    )
    instance.handle_new_event(_create_run_success_event(run_2.run_id, timestamp=6.0))

    # Verify check for partition "a" still returns True (partition isolation)
    record_a = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="a"
    )[check_key]
    ctx_2 = LoadingContextForTest(instance)
    assert asyncio.run(record_a.targets_latest_materialization(ctx_2)) is True

    # Materialize partition "a" again (M3) - should make check stale
    run_3 = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
    instance.event_log_storage.store_event(
        _create_materialization_event(run_3.run_id, asset_key, partition="a", timestamp=7.0)
    )
    instance.handle_new_event(_create_run_success_event(run_3.run_id, timestamp=8.0))

    # Verify check for partition "a" now returns False (newer mat exists for same partition)
    record_a = instance.event_log_storage.get_latest_asset_check_execution_by_key(
        [check_key], partition="a"
    )[check_key]
    ctx_3 = LoadingContextForTest(instance)
    assert asyncio.run(record_a.targets_latest_materialization(ctx_3)) is False
