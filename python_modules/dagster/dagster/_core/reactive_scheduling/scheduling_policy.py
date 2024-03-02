from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

from dagster import _check as check
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import PartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.instance import DagsterInstance
    from dagster._core.reactive_scheduling.asset_graph_view import (
        AssetGraphView,
        AssetSlice,
        AssetSliceFactory,
    )
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

    # tick settings in its own file?
    from .scheduling_sensor import SensorSpec


class SchedulingResult(NamedTuple):
    launch: bool = True
    asset_slice: Optional["AssetSlice"] = None


class EvaluationResult(NamedTuple):
    asset_slice: "AssetSlice"


class SchedulingPolicy:
    sensor_spec: Optional["SensorSpec"] = None

    # TODO: what about multi asset case?
    def tick(
        self, context: "SchedulingExecutionContext", asset_slice: "AssetSlice"
    ) -> SchedulingResult:
        """If there is a sensor spec, this gets evaluated on every tick."""
        ...

    # defaults to empty
    def evaluate(
        self, context: "SchedulingExecutionContext", current_slice: "AssetSlice"
    ) -> EvaluationResult:
        """Evaluate gets called as the scheduling algorithm traverses over the partition space in context."""
        return EvaluationResult(asset_slice=context.slice_factory.empty(current_slice.asset_key))


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
        from dagster._core.reactive_scheduling.asset_graph_view import (
            AssetGraphView,
            TemporalContext,
        )

        stale_status_resolver = CachingStaleStatusResolver(instance, repository_def.asset_graph)
        # create these on demand rather than the lazy BS
        check.invariant(stale_status_resolver.instance_queryer)
        check.inst(stale_status_resolver.asset_graph, InternalAssetGraph)
        return SchedulingExecutionContext(
            tick_dt=tick_dt,
            asset_graph_view=AssetGraphView(
                temporal_context=TemporalContext(current_dt=tick_dt, storage_id=last_storage_id),
                stale_resolver=stale_status_resolver,
            ),
            last_storage_id=last_storage_id,
        )

    # TODO can eliminate. Just get from asset_graph_view
    tick_dt: datetime
    asset_graph_view: "AssetGraphView"
    # TODO can eliminate. Just get from asset_graph_view
    last_storage_id: Optional[int] = None

    def empty_slice(self, asset_key: AssetKey) -> "AssetSlice":
        return self.slice_factory.empty(asset_key)

    @property
    def slice_factory(self) -> "AssetSliceFactory":
        return self.asset_graph_view.slice_factory

    @property
    def queryer(self) -> "CachingInstanceQueryer":
        return self.asset_graph_view.stale_resolver.instance_queryer

    @property
    def instance(self) -> "DagsterInstance":
        return self.queryer.instance

    @property
    def asset_graph(self) -> "InternalAssetGraph":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        assert isinstance(self.asset_graph_view.stale_resolver.asset_graph, InternalAssetGraph)
        return self.asset_graph_view.stale_resolver.asset_graph

    def get_scheduling_info(self, asset_key: AssetKey) -> AssetSchedulingInfo:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        return AssetSchedulingInfo(
            asset_key=asset_key,
            scheduling_policy=assets_def.scheduling_policies_by_key.get(asset_key),
            partitions_def=assets_def.partitions_def,
        )
