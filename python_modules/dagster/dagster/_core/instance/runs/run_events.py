import logging
from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluationPlanned,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARTITION_NAME_TAG,
)

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.base_asset_graph import (
        BaseAssetGraph,
        BaseAssetNode,
    )
    from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
    from dagster._core.snap import ExecutionPlanSnapshot
    from dagster._core.snap.execution_plan_snapshot import (
        ExecutionStepOutputSnap,
        ExecutionStepSnap,
    )


def log_asset_planned_events(
    ops: "RunInstanceOps",
    dagster_run: DagsterRun,
    execution_plan_snapshot: "ExecutionPlanSnapshot",
    asset_graph: "BaseAssetGraph",
) -> None:
    """Moved from DagsterInstance._log_asset_planned_events."""
    from dagster._core.events import DagsterEvent, DagsterEventType

    job_name = dagster_run.job_name

    for step in execution_plan_snapshot.steps:
        if step.key in execution_plan_snapshot.step_keys_to_execute:
            for output in step.outputs:
                asset_key = check.not_none(output.properties).asset_key
                if asset_key:
                    log_materialization_planned_event_for_asset(
                        ops, dagster_run, asset_key, job_name, step, output, asset_graph
                    )

                if check.not_none(output.properties).asset_check_key:
                    asset_check_key = check.not_none(
                        check.not_none(output.properties).asset_check_key
                    )
                    target_asset_key = asset_check_key.asset_key
                    check_name = asset_check_key.name

                    event = DagsterEvent(
                        event_type_value=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                        job_name=job_name,
                        message=(
                            f"{job_name} intends to execute asset check {check_name} on"
                            f" asset {target_asset_key.to_string()}"
                        ),
                        event_specific_data=AssetCheckEvaluationPlanned(
                            target_asset_key,
                            check_name=check_name,
                        ),
                        step_key=step.key,
                    )
                    ops.report_dagster_event(event, dagster_run.run_id, logging.DEBUG)


def log_materialization_planned_event_for_asset(
    ops: "RunInstanceOps",
    dagster_run: DagsterRun,
    asset_key: AssetKey,
    job_name: str,
    step: "ExecutionStepSnap",
    output: "ExecutionStepOutputSnap",
    asset_graph: "BaseAssetGraph[BaseAssetNode]",
) -> None:
    """Moved from DagsterInstance._log_materialization_planned_event_for_asset."""
    from dagster._core.definitions.partitions.context import partition_loading_context
    from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition
    from dagster._core.events import AssetMaterializationPlannedData, DagsterEvent

    partition_tag = dagster_run.tags.get(PARTITION_NAME_TAG)
    partition_range_start, partition_range_end = (
        dagster_run.tags.get(ASSET_PARTITION_RANGE_START_TAG),
        dagster_run.tags.get(ASSET_PARTITION_RANGE_END_TAG),
    )

    if partition_tag and (partition_range_start or partition_range_end):
        raise DagsterInvariantViolationError(
            f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
            f" {ASSET_PARTITION_RANGE_END_TAG} set along with"
            f" {PARTITION_NAME_TAG}"
        )

    partitions_subset = None
    individual_partitions = None
    if partition_range_start or partition_range_end:
        if not partition_range_start or not partition_range_end:
            raise DagsterInvariantViolationError(
                f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
                f" {ASSET_PARTITION_RANGE_END_TAG} set without the other"
            )

        partitions_def = asset_graph.get(asset_key).partitions_def
        if isinstance(partitions_def, DynamicPartitionsDefinition) and partitions_def.name is None:
            raise DagsterInvariantViolationError(
                "Creating a run targeting a partition range is not supported for assets partitioned with function-based dynamic partitions"
            )

        if partitions_def is not None:
            with partition_loading_context(
                dynamic_partitions_store=ops.as_dynamic_partitions_store()
            ):
                if ops.event_log_storage.supports_partition_subset_in_asset_materialization_planned_events:
                    partitions_subset = partitions_def.subset_with_partition_keys(
                        partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(partition_range_start, partition_range_end),
                        )
                    ).to_serializable_subset()
                    individual_partitions = []
                else:
                    individual_partitions = partitions_def.get_partition_keys_in_range(
                        PartitionKeyRange(partition_range_start, partition_range_end),
                    )
    elif check.not_none(output.properties).is_asset_partitioned and partition_tag:
        individual_partitions = [partition_tag]

    assert not (individual_partitions and partitions_subset), (
        "Should set either individual_partitions or partitions_subset, but not both"
    )

    if not individual_partitions and not partitions_subset:
        materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
            job_name,
            step.key,
            AssetMaterializationPlannedData(asset_key, partition=None, partitions_subset=None),
        )
        ops.report_dagster_event(materialization_planned, dagster_run.run_id, logging.DEBUG)
    elif individual_partitions:
        for individual_partition in individual_partitions:
            materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
                job_name,
                step.key,
                AssetMaterializationPlannedData(
                    asset_key,
                    partition=individual_partition,
                    partitions_subset=partitions_subset,
                ),
            )
            ops.report_dagster_event(materialization_planned, dagster_run.run_id, logging.DEBUG)
    else:
        materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
            job_name,
            step.key,
            AssetMaterializationPlannedData(
                asset_key, partition=None, partitions_subset=partitions_subset
            ),
        )
        ops.report_dagster_event(materialization_planned, dagster_run.run_id, logging.DEBUG)
