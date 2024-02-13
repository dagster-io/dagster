from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set, Union

from dagster import _check as check
from dagster._core.definitions.asset_daemon_context import build_run_requests
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.run_request import SensorResult, SkipReason
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.reactive_scheduling.reactive_policy import (
    AssetPartition,
    SchedulingPolicy,
    SchedulingResult,
)


@dataclass(frozen=True)
class ReactiveAssetInfo:
    asset_key: AssetKey
    assets_def: AssetsDefinition
    scheduling_policy: SchedulingPolicy


@dataclass(frozen=True)
class ReactivePlan:
    asset_partitions: Set[AssetPartition]


@dataclass(frozen=True)
class ReactiveRequestBuilder:
    repository_def: RepositoryDefinition
    asset_graph: AssetGraph
    dynamic_partitions_store: DynamicPartitionsStore
    current_time: datetime

    def get_latest_asset_subset_for_key(self, asset_key: AssetKey) -> ValidAssetSubset:
        assets_def = self.repository_def.assets_defs_by_key[asset_key]
        if not assets_def.partitions_def:
            return AssetSubset(asset_key, True).as_valid(assets_def.partitions_def)
        else:
            assert assets_def.partitions_def  # for pyright
            last_partition_key = assets_def.partitions_def.get_last_partition_key(
                current_time=self.current_time,
                dynamic_partitions_store=self.dynamic_partitions_store,
            )
            partitions_subset = assets_def.partitions_def.empty_subset()
            if last_partition_key:
                partitions_subset = partitions_subset.with_partition_keys([last_partition_key])
            return AssetSubset(asset_key, partitions_subset).as_valid(assets_def.partitions_def)

    def get_parent_asset_subset(
        self, asset_subset: ValidAssetSubset, parent_asset_key: AssetKey
    ) -> ValidAssetSubset:
        parent_assets_def = self.repository_def.assets_defs_by_key[parent_asset_key]
        return self.asset_graph.get_parent_asset_subset(
            child_asset_subset=asset_subset,
            parent_asset_key=parent_asset_key,
            dynamic_partitions_store=self.dynamic_partitions_store,
            current_time=self.current_time,
        ).as_valid(parent_assets_def.partitions_def)

    def get_child_asset_subset(
        self, asset_subset: ValidAssetSubset, child_asset_key: AssetKey
    ) -> ValidAssetSubset:
        child_assets_def = self.repository_def.assets_defs_by_key[child_asset_key]
        return self.asset_graph.get_child_asset_subset(
            parent_asset_subset=asset_subset,
            child_asset_key=child_asset_key,
            dynamic_partitions_store=self.dynamic_partitions_store,
            current_time=self.current_time,
        ).as_valid(child_assets_def.partitions_def)

    def build_plan(
        self,
        asset_key: AssetKey,
    ) -> ReactivePlan:
        # This is the core of the algorith. Assuming that tick has instructed the policy
        # to instigate a run, we build a plan. This algorithm walks up and down the asset
        # graph recursively, calling react_to_downstream_request and react_to_upstream_request
        # respectively. Through this we cooperatively build a set of run requests.
        start_asset_subset = self.get_latest_asset_subset_for_key(asset_key)
        return self.build_for_asset_subset(start_asset_subset)

    def build_for_asset_subset(self, start_asset_subset: ValidAssetSubset) -> ReactivePlan:
        visited: Set[AssetPartition] = set()
        asset_partitions_to_execute: Set[AssetPartition] = set()

        def _ascend(current_asset_subset: ValidAssetSubset):
            asset_partitions_to_execute.update(current_asset_subset.asset_partitions)
            visited.update(current_asset_subset.asset_partitions)
            for parent_asset_key in self.asset_graph.get_parents(current_asset_subset.asset_key):
                parent_asset_info = self.reactive_info_for_key(parent_asset_key)
                if not parent_asset_info:
                    continue

                parent_asset_subset = self.get_parent_asset_subset(
                    current_asset_subset, parent_asset_key
                )

                parent_result = parent_asset_info.scheduling_policy.react_to_downstream_request(
                    parent_asset_subset
                )
                if parent_result.execute:
                    asset_partitions_to_execute.update(parent_asset_subset.asset_partitions)
                    _ascend(parent_asset_subset)

        def _descend(current_asset_subset: ValidAssetSubset):
            asset_partitions_to_execute.update(current_asset_subset.asset_partitions)
            visited.update(current_asset_subset.asset_partitions)

            for child_asset_key in self.asset_graph.get_children(current_asset_subset.asset_key):
                child_asset_info = self.reactive_info_for_key(child_asset_key)
                if not child_asset_info:
                    continue

                child_asset_subset = self.get_child_asset_subset(
                    current_asset_subset, child_asset_key
                )

                child_result = child_asset_info.scheduling_policy.react_to_upstream_request(
                    child_asset_subset
                )

                if child_result.execute:
                    asset_partitions_to_execute.update(child_asset_subset.asset_partitions)
                    _descend(child_asset_subset)

        _ascend(start_asset_subset)
        _descend(start_asset_subset)

        return ReactivePlan(asset_partitions_to_execute)

    def make_valid_subset(
        self, asset_key: AssetKey, asset_partitions: Set[AssetPartition]
    ) -> ValidAssetSubset:
        assets_def = self.repository_def.assets_defs_by_key[asset_key]
        return AssetSubset.from_asset_partitions_set(
            asset_key=asset_key,
            asset_partitions_set=asset_partitions,
            partitions_def=assets_def.partitions_def,
        )

    def reactive_info_for_key(self, asset_key: AssetKey) -> Optional[ReactiveAssetInfo]:
        assets_def = self.repository_def.assets_defs_by_key[asset_key]
        scheduling_policy = assets_def.scheduling_policy_by_key.get(asset_key)

        return (
            ReactiveAssetInfo(
                asset_key=asset_key, assets_def=assets_def, scheduling_policy=scheduling_policy
            )
            if scheduling_policy
            else None
        )


def reactive_asset_info_for_key(
    context: SensorEvaluationContext, asset_key: AssetKey
) -> Optional[ReactiveAssetInfo]:
    check.invariant(context.repository_def, "SensorEvaluationContext must have a repository_def")
    assert context.repository_def
    assets_def = context.repository_def.assets_defs_by_key[asset_key]
    scheduling_policy = assets_def.scheduling_policy_by_key.get(asset_key)
    return (
        ReactiveAssetInfo(
            asset_key=asset_key, assets_def=assets_def, scheduling_policy=scheduling_policy
        )
        if scheduling_policy
        else None
    )


def make_valid_subset_from_result(
    scheduling_result: SchedulingResult, asset_key: AssetKey, assets_def: AssetsDefinition
) -> ValidAssetSubset:
    if scheduling_result.partition_keys is None:
        return AssetSubset(asset_key=asset_key, value=True).as_valid(assets_def.partitions_def)
    else:
        return AssetSubset(
            asset_key=asset_key, value=DefaultPartitionsSubset(scheduling_result.partition_keys)
        ).as_valid(assets_def.partitions_def)


def build_reactive_scheduling_sensor(
    assets_def: AssetsDefinition, asset_key: AssetKey
) -> SensorDefinition:
    check.invariant(asset_key in assets_def.scheduling_policy_by_key)
    scheduling_policy = assets_def.scheduling_policy_by_key[asset_key]

    @sensor(
        name=scheduling_policy.sensor_name
        if scheduling_policy.sensor_name
        else f"{asset_key.to_python_identifier()}_reactive_scheduling_sensor",
        minimum_interval_seconds=10,
        default_status=DefaultSensorStatus.RUNNING,
        asset_selection="*",
    )
    def sensor_fn(context: SensorEvaluationContext) -> Union[SensorResult, SkipReason]:
        check.invariant(
            context.repository_def, "SensorEvaluationContext must have a repository_def"
        )
        assert context.repository_def

        scheduling_result = scheduling_policy.schedule()

        if not scheduling_result.execute:
            return SkipReason(
                skip_message=f"Scheduling policy for {asset_key.to_user_string()} did not request execution"
            )

        builder = ReactiveRequestBuilder(
            asset_graph=context.repository_def.asset_graph,
            dynamic_partitions_store=context.instance,
            current_time=datetime.now(),
            repository_def=context.repository_def,
        )

        root_subset = make_valid_subset_from_result(scheduling_result, asset_key, assets_def)

        reactive_plan = builder.build_for_asset_subset(root_subset)

        run_requests = build_run_requests(
            asset_partitions=reactive_plan.asset_partitions,
            asset_graph=builder.asset_graph,
            run_tags={},
        )

        return SensorResult(run_requests=run_requests)

    return sensor_fn
