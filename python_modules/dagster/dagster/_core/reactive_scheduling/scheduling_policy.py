from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.instance import DagsterInstance
    from dagster._core.reactive_scheduling.asset_graph_traverser import AssetGraphTraverser
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

AssetPartition: TypeAlias = AssetKeyPartitionKey


class SchedulingResult(NamedTuple):
    launch: bool = True


class TickSettings(NamedTuple):
    tick_cron: str = "* * * * *"
    sensor_name: Optional[str] = None
    sensor_description: Optional[str] = None


class EvaluationResult(NamedTuple):
    asset_subset: ValidAssetSubset


class SchedulingPolicy:
    # TODO: what about multi asset case?
    def tick(self, context: "SchedulingExecutionContext") -> SchedulingResult:
        ...

    # defaults to empty
    def evaluate(
        self, context: "SchedulingExecutionContext", current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(
            asset_subset=AssetSubset.empty(
                current_subset.asset_key,
                context.asset_graph.get_assets_def(current_subset.asset_key).partitions_def,
            )
        )


class AssetSchedulingInfo(NamedTuple):
    asset_key: AssetKey
    scheduling_policy: Optional[SchedulingPolicy]
    partitions_def: Optional[PartitionsDefinition]

    def __repr__(self) -> str:
        return f"AssetSchedulingInfo(asset_key={self.asset_key}, scheduling_policy={self.scheduling_policy}, partitions_def={self.partitions_def})"


class SchedulingExecutionContext(NamedTuple):
    @staticmethod
    def create(
        instance: "DagsterInstance",
        repository_def: "RepositoryDefinition",
        tick_dt: datetime,
        last_storage_id: Optional[int],
    ) -> "SchedulingExecutionContext":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
        from dagster._core.reactive_scheduling.asset_graph_traverser import AssetGraphTraverser

        stale_status_resolver = CachingStaleStatusResolver(instance, repository_def.asset_graph)
        # create these on demand rather than the lazy BS
        check.invariant(stale_status_resolver.instance_queryer)
        check.inst(stale_status_resolver.asset_graph, InternalAssetGraph)
        return SchedulingExecutionContext(
            tick_dt=tick_dt,
            traverser=AssetGraphTraverser(stale_status_resolver, current_dt=tick_dt),
            last_storage_id=last_storage_id,
        )

    tick_dt: datetime
    traverser: "AssetGraphTraverser"
    last_storage_id: Optional[int] = None

    def empty_subset(self, asset_key: AssetKey) -> ValidAssetSubset:
        return ValidAssetSubset.empty(
            asset_key, self.asset_graph.get_assets_def(asset_key).partitions_def
        )

    @property
    def queryer(self) -> "CachingInstanceQueryer":
        return self.traverser.stale_resolver.instance_queryer

    @property
    def instance(self) -> "DagsterInstance":
        return self.queryer.instance

    @property
    def asset_graph(self) -> "InternalAssetGraph":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        assert isinstance(self.traverser.stale_resolver.asset_graph, InternalAssetGraph)
        return self.traverser.stale_resolver.asset_graph

    def get_scheduling_info(self, asset_key: AssetKey) -> AssetSchedulingInfo:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        return AssetSchedulingInfo(
            asset_key=asset_key,
            scheduling_policy=assets_def.scheduling_policies_by_key.get(asset_key),
            partitions_def=assets_def.partitions_def,
        )
