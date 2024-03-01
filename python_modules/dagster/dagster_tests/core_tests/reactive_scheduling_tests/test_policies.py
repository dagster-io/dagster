from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional, Set

import pendulum
from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.asset_graph_view import (
    AssetPartition,
    AssetSlice,
)
from dagster._core.reactive_scheduling.scheduling_plan import Rules
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._core.reactive_scheduling.scheduling_sensor import SensorSpec
from dagster._core.storage.dagster_run import RunsFilter


class AlwaysIncludeSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


class NeverIncludeSchedulingPolicy(SchedulingPolicy):
    ...


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def __init__(self, sensor_spec: SensorSpec):
        self.sensor_spec = sensor_spec

    def tick(
        self, context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> SchedulingResult:
        return SchedulingResult(launch=True)

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


class AlwaysLaunchLatestTimeWindowSchedulingPolicy(SchedulingPolicy):
    def __init__(self, sensor_spec: SensorSpec):
        self.sensor_spec = sensor_spec

    def tick(
        self, context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> SchedulingResult:
        return SchedulingResult(launch=True, asset_slice=asset_slice.latest_complete_time_window)

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=Rules.latest_time_window(context, current_slice))


class LatestRequiredRunTags(SchedulingPolicy):
    def __init__(self, latest_run_required_tags: Dict[str, str]):
        self.latest_run_required_tags = latest_run_required_tags

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        if not all(record for record in current_slice.records_by_asset_partition.values()):
            return EvaluationResult(asset_slice=context.empty_slice(current_slice.asset_key))

        asset_partitions_by_latest_run_id: Dict[str, Set[AssetPartition]] = defaultdict(set)

        for asset_partition, record in current_slice.records_by_asset_partition.items():
            asset_partitions_by_latest_run_id[check.not_none(record).run_id].add(asset_partition)

        if not asset_partitions_by_latest_run_id:
            return EvaluationResult(asset_slice=context.empty_slice(current_slice.asset_key))

        run_ids_with_required_tags = context.instance.get_run_ids(
            filters=RunsFilter(
                run_ids=list(asset_partitions_by_latest_run_id.keys()),
                tags=self.latest_run_required_tags,
            )
        )

        updated_partitions_with_required_tags = {
            asset_partition
            for run_id, run_id_asset_partitions in asset_partitions_by_latest_run_id.items()
            if run_id in run_ids_with_required_tags
            for asset_partition in run_id_asset_partitions
        }

        return EvaluationResult(
            context.slice_factory.from_asset_partitions(updated_partitions_with_required_tags)
            if updated_partitions_with_required_tags
            else context.slice_factory.empty(current_slice.asset_key)
        )


def build_test_context(
    defs: Definitions,
    instance: Optional[DagsterInstance] = None,
    tick_dt: Optional[datetime] = None,
    last_storage_id: Optional[int] = None,
) -> SchedulingExecutionContext:
    return SchedulingExecutionContext.create(
        instance=instance or DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
        tick_dt=tick_dt or pendulum.now(),
        last_storage_id=last_storage_id,
    )


def slices_equal(left_slice: AssetSlice, right_slice: AssetSlice) -> bool:
    left = left_slice.to_valid_asset_subset()
    right = right_slice.to_valid_asset_subset()
    if left.asset_key != right.asset_key:
        return False
    if left.is_partitioned and right.is_partitioned:
        return set(left.subset_value.get_partition_keys()) == set(
            right.subset_value.get_partition_keys()
        )
    elif not left.is_partitioned and not right.is_partitioned:
        return left.bool_value == right.bool_value
    else:
        check.failed("should not get here with valid subsets")
