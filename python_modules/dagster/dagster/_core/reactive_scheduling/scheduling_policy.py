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

    from .expr import ExprNode
    from .scheduling_sensor import SensorSpec


class ScheduleLaunchResult(NamedTuple):
    launch: bool = True
    explicit_launching_slice: Optional["AssetSlice"] = None
    cursor: Optional[str] = None


class EvaluationResult(NamedTuple):
    asset_slice: "AssetSlice"


class SchedulingPolicy:
    def __init__(
        self, sensor_spec: Optional["SensorSpec"] = None, expr: Optional["ExprNode"] = None
    ):
        self.sensor_spec = sensor_spec
        self.expr = expr

    def schedule_launch(
        self, context: "SchedulingExecutionContext", asset_slice: "AssetSlice"
    ) -> ScheduleLaunchResult:
        """If there is a sensor spec, this gets evaluated on every tick."""
        ...

    # defaults to honoring expr or empty if there is no expr
    def evaluate(
        self, context: "SchedulingExecutionContext", current_slice: "AssetSlice"
    ) -> EvaluationResult:
        """Evaluate gets called as the scheduling algorithm traverses over the partition space in context."""
        return EvaluationResult(
            asset_slice=self.expr.evaluate(context, current_slice)
            if self.expr
            else context.slice_factory.empty(current_slice.asset_key)
        )

    @staticmethod
    def for_expr(expr: "ExprNode"):
        return SchedulingPolicy(expr=expr)


class AssetSchedulingInfo(NamedTuple):
    asset_key: AssetKey
    scheduling_policy: Optional[SchedulingPolicy]
    partitions_def: Optional[PartitionsDefinition]

    def __repr__(self) -> str:
        return f"AssetSchedulingInfo(asset_key={self.asset_key}, scheduling_policy={self.scheduling_policy}, partitions_def={self.partitions_def})"


class SchedulingExecutionContext(NamedTuple):
    asset_graph_view: "AssetGraphView"
    # todo remove default
    previous_cursor: Optional[str] = None

    @staticmethod
    def create(
        instance: "DagsterInstance",
        repository_def: "RepositoryDefinition",
        effective_dt: datetime,
        last_event_id: Optional[int],
        # todo  remove default
        previous_cursor: Optional[str] = None,
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
            asset_graph_view=AssetGraphView(
                temporal_context=TemporalContext(
                    effective_dt=effective_dt, last_event_id=last_event_id
                ),
                stale_resolver=stale_status_resolver,
            ),
            previous_cursor=previous_cursor,
        )

    @property
    def effective_dt(self) -> datetime:
        return self.asset_graph_view.temporal_context.effective_dt

    @property
    def last_event_id(self) -> Optional[int]:
        return self.asset_graph_view.temporal_context.last_event_id

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

        check.inst(self.asset_graph_view.stale_resolver.asset_graph, InternalAssetGraph)
        assert isinstance(self.asset_graph_view.stale_resolver.asset_graph, InternalAssetGraph)
        return self.asset_graph_view.stale_resolver.asset_graph

    def get_scheduling_info(self, asset_key: AssetKey) -> AssetSchedulingInfo:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        return AssetSchedulingInfo(
            asset_key=asset_key,
            scheduling_policy=assets_def.scheduling_policies_by_key.get(asset_key),
            partitions_def=assets_def.partitions_def,
        )
