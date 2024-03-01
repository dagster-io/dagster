import itertools
from collections import defaultdict
from datetime import datetime
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
)

import pendulum
from typing_extensions import TypeAlias

from dagster import (
    _check as check,
)
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.data_version import StaleStatus
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
    from dagster._core.definitions.data_version import CachingStaleStatusResolver
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
    from dagster._core.event_api import EventLogRecord
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
AssetPartition: TypeAlias = AssetKeyPartitionKey

PartitionKey: TypeAlias = Optional[str]


class AssetSlice:
    """Represents a set of partition (i.e. a slice) of an asset at a point in time. Can be used to explore
    the entire asset graph from a particular starting point.
    """

    def __init__(self, asset_graph_view: "AssetGraphView", valid_asset_subset: ValidAssetSubset):
        self._asset_graph_view = asset_graph_view
        self._valid_asset_subset = valid_asset_subset

    @property
    def asset_key(self) -> AssetKey:
        return self._valid_asset_subset.asset_key

    def to_valid_asset_subset(self) -> ValidAssetSubset:
        return self._valid_asset_subset

    # This is very expensive and should not be done during plan build. Likely need to hide
    def materialize_partition_keys(self) -> Set[PartitionKey]:
        return set(ap.partition_key for ap in self._valid_asset_subset.asset_partitions)

    # This is very expensive and should not be done during plan build. Likely need to hide
    def materialize_asset_partitions(self) -> AbstractSet[AssetPartition]:
        return self._valid_asset_subset.asset_partitions

    @property
    def empty(self) -> bool:
        return self._valid_asset_subset.is_empty

    @property
    def nonempty(self) -> bool:
        return not self.empty

    @property
    def has_single_time_window(self) -> bool:
        return (
            isinstance(self._partitions_def, TimeWindowPartitionsDefinition)
            and isinstance(self._valid_asset_subset.subset_value, TimeWindowPartitionsSubset)
            and len(self._valid_asset_subset.subset_value.included_time_windows) == 1
        )

    @property
    def time_window(self) -> TimeWindow:
        # not guaranteed to work but extraordinarily convenient
        check.invariant(self.has_single_time_window, "Must have a single time window")
        # for typechecker
        assert isinstance(self._valid_asset_subset.subset_value, TimeWindowPartitionsSubset)
        return next(iter(self._valid_asset_subset.subset_value.included_time_windows))

    @cached_property
    def _partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._asset_graph_view.asset_graph.get_assets_def(self.asset_key).partitions_def

    @cached_property
    def parent_parition_space(self) -> "PartitionSpace":
        return self._asset_graph_view.parent_partition_space(self)

    @cached_property
    # could alteratively be an updated property on partition space itself
    # e.g. parent_partition_space.updated
    def updated_parent_partition_space(self) -> "UpstreamPartitionSpace":
        return self._asset_graph_view.updated_upstream_partition_space(self)

    @cached_property
    def unsynced(self) -> "AssetSlice":
        return self._asset_graph_view.unsynced_slice(self)

    # @cached_property
    # def unsynced_parent_partition_space(self) -> "PartitionSpace":
    #     return self._asset_graph_view.unsynced_slice(self)

    # TODO: should event log record be public
    # TODO: prefetch this. ends up calling _get_latest_materialization_or_observation_record on
    # a single asset partition in CachingInstanceQueryer
    @cached_property
    def records_by_asset_partition(self) -> Dict[AssetPartition, Optional["EventLogRecord"]]:
        records_by_asset_partition = {}
        for asset_partition in self.materialize_asset_partitions():
            records_by_asset_partition[
                asset_partition
            ] = self._asset_graph_view.queryer.get_latest_materialization_or_observation_record(
                asset_partition, before_cursor=self._asset_graph_view.temporal_context.storage_id
            )
        return records_by_asset_partition

    def total_parent_asset_slice(self, parent_asset_key: AssetKey) -> "AssetSlice":
        for asset_slice in self.total_parent_slices:
            if asset_slice.asset_key == parent_asset_key:
                return asset_slice

        check.failed(f"Parent asset {parent_asset_key} not found in {self}")

    def parent_slice_of_partition_key(
        self, parent_asset_key: AssetKey, partition_key: PartitionKey
    ) -> "AssetSlice":
        return self._asset_graph_view.get_parent_asset_slice(
            parent_asset_key=parent_asset_key,
            asset_slice=AssetSlice(
                self._asset_graph_view,
                ValidAssetSubset.from_asset_partitions_set(
                    asset_key=self.asset_key,
                    partitions_def=self._partitions_def,
                    asset_partitions_set={AssetPartition(self.asset_key, partition_key)},
                ),
            ),
        )

    @cached_property
    def total_parent_slices(self) -> List["AssetSlice"]:
        return [
            self._asset_graph_view.get_parent_asset_slice(parent_key, self)
            for parent_key in self._asset_graph_view.asset_graph.get_parents(self.asset_key)
        ]

    @cached_property
    def latest_complete_time_window(self) -> "AssetSlice":
        partitions_def = self._partitions_def
        if self._partitions_def is None:
            return self

        if isinstance(partitions_def, StaticPartitionsDefinition):
            return self

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            time_window = partitions_def.get_last_partition_window(
                self._asset_graph_view.current_dt
            )
            return (
                self._asset_graph_view.slice_factory.from_time_window(self.asset_key, time_window)
                if time_window
                else self._asset_graph_view.slice_factory.empty(self.asset_key)
            )

        # Need to handle dynamic and multi-dimensional partitioning
        check.failed(f"Unsupported partitions_def: {partitions_def}")

    ## operators

    def intersection(self, other: "AssetSlice") -> "AssetSlice":
        return AssetSlice(
            self._asset_graph_view,
            self._valid_asset_subset & other._valid_asset_subset,  # noqa
        )

    def equals(self, other: "AssetSlice") -> bool:
        # TODO: check asset_graph_view object identity?
        return self._valid_asset_subset == other._valid_asset_subset  # noqa

    def __repr__(self) -> str:
        return f"AssetSlice({self._valid_asset_subset})"


# An object that represents a point in time pinned to a particular storage id
# If storage_id is None, we consider this context to be volatile with respect to storage
# queries to the underlying instance will reflect the results of mutations that have occurred
# in real time
# Notesss
# * This might be overambitious, as I am not sure if all of our different storage can actually
#   respect storage_id. DynamicPartitionsTable for example does not appear to have enough information
#   to respect this, depending on the exact semantics of the create_timestamp column. Dynamic
#   partition creation is unfortunately not in the event log, so we can't use that to determine
#   storage_id .
# * Many of our underlying code paths do not support storage_id, if it is in the underlying table
#   until that is true some of the public functions will not respect storage_id and therefore be
#   de facto volatile.
class TemporalContext(NamedTuple):
    current_dt: datetime
    storage_id: Optional[int]


class AssetGraphView:
    """The AssetGraphView is a partition-native view of the asset graph at a particular point in time. It caches
    results. If a mutation occurs to the asset graph or an advance in time that you want to reflect within the process
    via a AssetGraphView, you need to create a new AssetGraphView with a new TemporalContext.

    Theorectically, this should allow for complete time-travel allowing the user to explore the completely
    partition space of an asset graph at any given point in time and state of the underlying instance.
    """

    def __init__(
        self,
        *,
        temporal_context: TemporalContext,
        # stale resolve has a CachingInstanceQueryer which has a DagsterInstance
        # so just passing the CachingStaleStatusResolver is enough
        stale_resolver: "CachingStaleStatusResolver",
    ):
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        assert isinstance(stale_resolver.asset_graph, InternalAssetGraph)
        check.inst(stale_resolver.asset_graph, InternalAssetGraph)
        # ensure it is already constructed rather than created on demand
        check.invariant(stale_resolver._instance_queryer)  # noqa

        self.asset_graph = stale_resolver.asset_graph
        self.stale_resolver = stale_resolver
        self.temporal_context = temporal_context

    @property
    def current_dt(self) -> datetime:
        return self.temporal_context.current_dt

    @property
    def queryer(self) -> "CachingInstanceQueryer":
        return self.stale_resolver.instance_queryer

    @staticmethod
    def for_test(
        defs: "Definitions",
        instance: Optional["DagsterInstance"] = None,
        current_dt: Optional[datetime] = None,
        last_storage_id: Optional[int] = None,
    ):
        from dagster._core.definitions.data_version import CachingStaleStatusResolver
        from dagster._core.instance import DagsterInstance

        return AssetGraphView(
            temporal_context=TemporalContext(
                current_dt=current_dt or pendulum.now(),
                storage_id=last_storage_id,
            ),
            stale_resolver=CachingStaleStatusResolver(
                instance=instance or DagsterInstance.ephemeral(),
                asset_graph=defs.get_repository_def().asset_graph,
            ),
        )

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.asset_graph.get_assets_def(asset_key).partitions_def

    def _to_asset_slice(self, asset_subset: ValidAssetSubset) -> AssetSlice:
        return AssetSlice(self, asset_subset)

    def get_parent_asset_slice(
        self, parent_asset_key: AssetKey, asset_slice: AssetSlice
    ) -> AssetSlice:
        return self._to_asset_slice(
            self.asset_graph.get_parent_asset_subset(
                dynamic_partitions_store=self.queryer,
                parent_asset_key=parent_asset_key,
                child_asset_subset=asset_slice.to_valid_asset_subset(),
                current_time=self.current_dt,
            )
        )

    def child_asset_slice(self, child_asset_key: AssetKey, asset_slice: AssetSlice) -> AssetSlice:
        return self._to_asset_slice(
            self.asset_graph.get_child_asset_subset(
                dynamic_partitions_store=self.queryer,
                child_asset_key=child_asset_key,
                parent_asset_subset=asset_slice.to_valid_asset_subset(),
                current_time=self.current_dt,
            )
        )

    def parent_partition_space(self, asset_slice: AssetSlice) -> "PartitionSpace":
        parent_parition_space = PartitionSpace.empty(self)
        for parent_slice in asset_slice.total_parent_slices:
            parent_parition_space = parent_parition_space.with_asset_slice(parent_slice)
        return parent_parition_space

    def updated_upstream_partition_space(
        self, current_slice: AssetSlice
    ) -> "UpstreamPartitionSpace":
        upstream_space_builder = UpstreamPartitionSpaceBuilder(self, current_slice)

        for child_asset_partition in current_slice.materialize_asset_partitions():
            parents_asset_partitions = self.asset_graph.get_parents_partitions(
                self.queryer,
                self.temporal_context.current_dt,
                child_asset_partition.asset_key,
                child_asset_partition.partition_key,
            ).parent_partitions

            updated_parent_asset_partitions = self.queryer.get_parent_asset_partitions_updated_after_child(
                child_asset_partition,
                parents_asset_partitions,
                respect_materialization_data_versions=True,
                # In equilvalent code path in AMP there is the following comment:
                # ********
                # do a precise check for updated parents, factoring in data versions, as long as
                # we're within reasonable limits on the number of partitions to check
                # respect_materialization_data_versions=context.daemon_context.respect_materialization_data_versions
                # and len(parent_asset_partitions) + subset_to_evaluate.size < 100,
                # ********
                # I think we can get away with not doing this if we impose constraints about the number
                # of partitions to consider in any particular tick (Unless user opts into it)
                #
                # ignore self-dependencies when checking for updated parents, to avoid historical
                # rematerializations from causing a chain of materializations to be kicked off
                # Question: do I understand this?
                ignored_parent_keys={current_slice.asset_key},
            )

            upstream_space_builder.add_mappings(
                child_asset_partition.partition_key, updated_parent_asset_partitions
            )

        return upstream_space_builder.build()

    def unsynced_slice(self, asset_slice: AssetSlice) -> "AssetSlice":
        unsynced_pks = set()
        for partition_key in asset_slice.materialize_partition_keys():
            stale_status = self.stale_resolver.get_status(asset_slice.asset_key, partition_key)
            if stale_status != StaleStatus.FRESH:
                unsynced_pks.add(partition_key)

        return self.slice_factory.from_partition_keys(asset_slice.asset_key, unsynced_pks)

    # broken
    def unsynced_parent_partition_space(self, asset_slice: AssetSlice) -> "PartitionSpace":
        upstream_space_builder = UpstreamPartitionSpaceBuilder(self, asset_slice)

        # Issues:
        # * This is going to be very slow
        # * get_status does not respect storage_id and will always be volatile
        unsynced_parent_asset_partitions: Set[AssetPartition] = set()
        for parent_slice in asset_slice.total_parent_slices:
            # materialize call is the indication that we are doing something wrong
            for parent_asset_partition in parent_slice.materialize_asset_partitions():
                stale_status = self.stale_resolver.get_status(
                    parent_asset_partition.asset_key, parent_asset_partition.partition_key
                )
                if stale_status != StaleStatus.FRESH:
                    upstream_space_builder.add_mapping(
                        parent_asset_partition.partition_key, parent_asset_partition
                    )
                    unsynced_parent_asset_partitions.add(parent_asset_partition)
        return PartitionSpace.from_asset_partitions(self, unsynced_parent_asset_partitions)

    def _create_upstream_asset_graph_subset(
        self, starting_asset_slice: AssetSlice
    ) -> "AssetGraphSubset":
        ag_subset = _graph_subset_from_slice(starting_asset_slice)

        def _ascend(current_slice: AssetSlice) -> None:
            nonlocal ag_subset
            for parent_slice in current_slice.total_parent_slices:
                # TODO can check to see if parent is already in subset and early return
                ag_subset |= _graph_subset_from_slice(parent_slice)
                _ascend(parent_slice)

        _ascend(starting_asset_slice)
        return ag_subset

    def create_upstream_partition_space(self, asset_slice: AssetSlice) -> "PartitionSpace":
        return PartitionSpace(self, self._create_upstream_asset_graph_subset(asset_slice))

    def get_parent_slices(self, asset_key) -> Sequence[AssetSlice]:
        return [self.get_parent_asset_slice(asset_key, child_slice) for child_slice in asset_key]

    @cached_property
    def slice_factory(self) -> "AssetSliceFactory":
        return AssetSliceFactory(self)


class UpstreamPartitionSpace:
    def __init__(
        self,
        asset_graph_view: "AssetGraphView",
        child_slice: AssetSlice,
        parent_slices_by_partition_key: Dict[PartitionKey, AssetSlice],
    ):
        self.asset_graph_view = asset_graph_view
        self.child_slice = child_slice
        self.parent_slices_by_partition_key = parent_slices_by_partition_key

    def compute_filtered_slice(
        self, slice_predicate: Callable[[AssetPartition, AssetSlice], bool]
    ) -> AssetSlice:
        pks: Set[PartitionKey] = set()
        for pk, parent_slice in self.parent_slices_by_partition_key.items():
            if slice_predicate(AssetPartition(self.child_slice.asset_key, pk), parent_slice):
                pks.add(pk)

        return self.asset_graph_view.slice_factory.from_partition_keys(
            self.child_slice.asset_key, pks
        )


class UpstreamPartitionSpaceBuilder:
    child_pk_to_parent_ak_to_parent_pk_set: Dict[PartitionKey, Dict[AssetKey, Set[PartitionKey]]]

    def __init__(self, asset_graph_view: AssetGraphView, child_slice: AssetSlice) -> None:
        self.asset_graph_view = asset_graph_view
        self.child_slice = child_slice
        self.child_pk_to_parent_ak_to_parent_pk_set = defaultdict(lambda: defaultdict(set))

    def add_mappings(
        self, child_key: PartitionKey, parent_aps: AbstractSet[AssetPartition]
    ) -> None:
        for parent_ap in parent_aps:
            self.add_mapping(child_key, parent_ap)

    def add_mapping(self, child_key: PartitionKey, parent_ap: AssetPartition) -> None:
        self.child_pk_to_parent_ak_to_parent_pk_set[child_key][parent_ap.asset_key].add(
            parent_ap.partition_key
        )

    def build(self) -> "UpstreamPartitionSpace":
        parent_slices = {}
        for (
            child_pk,
            parent_ak_to_pk_set,
        ) in self.child_pk_to_parent_ak_to_parent_pk_set.items():
            for parent_asset_key, parent_partition_keys in parent_ak_to_pk_set.items():
                parent_slices[child_pk] = self.asset_graph_view.slice_factory.from_partition_keys(
                    parent_asset_key, parent_partition_keys
                )

        return UpstreamPartitionSpace(self.asset_graph_view, self.child_slice, parent_slices)


# TODO: make thie space-efficient with __slots__ or something
class PartitionSpace:
    """Represents a partition-native subset of particular asset graph."""

    def __init__(self, asset_graph_view: AssetGraphView, asset_graph_subset: "AssetGraphSubset"):
        self.asset_graph_view = asset_graph_view
        self.asset_graph = asset_graph_view.asset_graph
        self.asset_graph_subset = asset_graph_subset

    @staticmethod
    def empty(asset_graph_view: AssetGraphView) -> "PartitionSpace":
        from dagster._core.definitions.asset_graph_subset import AssetGraphSubset

        return PartitionSpace(asset_graph_view, AssetGraphSubset())

    @staticmethod
    # Something has probably gone wrong if you are calling this as you have gone from subset-native to asset-partition-based and back
    def from_asset_partitions(
        asset_graph_view: AssetGraphView, asset_partitions: AbstractSet[AssetPartition]
    ) -> "PartitionSpace":
        from dagster._core.definitions.asset_graph_subset import AssetGraphSubset

        return PartitionSpace(
            asset_graph_view,
            AssetGraphSubset.from_asset_partition_set(
                asset_partitions, asset_graph_view.asset_graph
            ),
        )

    def for_keys(self, asset_keys: AbstractSet[AssetKey]) -> "PartitionSpace":
        return PartitionSpace(
            self.asset_graph_view, self.asset_graph_subset.filter_asset_keys(asset_keys)
        )

    @property
    def is_empty(self) -> bool:
        return self.asset_graph_subset.num_partitions_and_non_partitioned_assets == 0

    @cached_property
    def asset_keys(self) -> Set[AssetKey]:
        return set(self.asset_graph_subset.asset_keys)

    @cached_property
    def root_asset_keys(self) -> Set[AssetKey]:
        roots = set()
        subset_asset_keys = self.asset_graph_subset.asset_keys
        for asset_key in subset_asset_keys:
            if not any(
                parent_key in subset_asset_keys
                for parent_key in self.asset_graph.get_parents(asset_key)
            ):
                roots.add(asset_key)
        return roots

    @property
    def toposort_asset_keys(self) -> List[AssetKey]:
        return list(itertools.chain(*self.toposort_asset_levels))

    @cached_property
    def toposort_asset_levels(self) -> Sequence[AbstractSet[AssetKey]]:
        subset_asset_keys = self.asset_graph_subset.asset_keys
        filtered_levels = []
        for level in self.asset_graph.toposort_asset_keys():
            filtered_level = {key for key in level if key in subset_asset_keys}
            if filtered_level:
                filtered_levels.append(filtered_level)
        return filtered_levels

    def with_partition_space(self, other: "PartitionSpace") -> "PartitionSpace":
        return PartitionSpace(
            self.asset_graph_view, self.asset_graph_subset | other.asset_graph_subset
        )

    def with_asset_slice(self, asset_slice: AssetSlice) -> "PartitionSpace":
        return PartitionSpace(
            self.asset_graph_view,
            self.asset_graph_subset | _graph_subset_from_slice(asset_slice),
        )

    # TODO: probably should cache but cached_method only supports kwargs, which is annoying
    def get_asset_slice(self, asset_key: AssetKey) -> AssetSlice:
        return self.asset_graph_view._to_asset_slice(self._get_asset_subset(asset_key))  # noqa

    def _get_asset_subset(self, asset_key: AssetKey) -> ValidAssetSubset:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        if assets_def.partitions_def is None:
            return AssetSubset(
                asset_key=asset_key,
                value=asset_key in self.asset_graph_subset.non_partitioned_asset_keys,
            ).as_valid(assets_def.partitions_def)
        else:
            return AssetSubset(
                asset_key=asset_key,
                value=self.asset_graph_subset.partitions_subsets_by_asset_key.get(
                    asset_key, assets_def.partitions_def.empty_subset()
                ),
            ).as_valid(assets_def.partitions_def)

    def __repr__(self) -> str:
        return "PartitionSpace(" f"asset_graph_subset={self.asset_graph_subset}" ")"


def _graph_subset_from_slice(asset_slice: AssetSlice) -> "AssetGraphSubset":
    from dagster._core.definitions.asset_graph_subset import AssetGraphSubset

    asset_subset = asset_slice.to_valid_asset_subset()
    if asset_subset.is_partitioned:
        return AssetGraphSubset(
            partitions_subsets_by_asset_key={asset_subset.asset_key: asset_subset.subset_value}
        )
    else:
        return AssetGraphSubset(
            non_partitioned_asset_keys=(
                {asset_subset.asset_key} if asset_subset.bool_value else set()
            )
        )


class AssetSliceFactory:
    def __init__(self, asset_graph_view: AssetGraphView):
        self.asset_graph_view = asset_graph_view

    @property
    def asset_graph(self) -> "InternalAssetGraph":
        return self.asset_graph_view.asset_graph

    def empty(self, asset_key: AssetKey) -> AssetSlice:
        return AssetSlice(
            self.asset_graph_view,
            ValidAssetSubset.empty(
                asset_key, self.asset_graph.get_assets_def(asset_key).partitions_def
            ),
        )

    def unpartitioned(self, asset_key: AssetKey) -> AssetSlice:
        return self._to_asset_slice(asset_key=asset_key, value=True)

    # unclear if this should even be a method. Should get down to single asset key abstraction
    # before getting here
    def from_asset_partitions(self, asset_partitions: AbstractSet[AssetPartition]) -> AssetSlice:
        partition_space = PartitionSpace.from_asset_partitions(
            self.asset_graph_view, asset_partitions
        )
        check.invariant(len(partition_space.asset_keys) == 1)
        return partition_space.get_asset_slice(next(iter(partition_space.asset_keys)))

    def from_partition_keys(
        self, asset_key: AssetKey, partition_keys: AbstractSet[PartitionKey]
    ) -> AssetSlice:
        if not partition_keys:
            return self.empty(asset_key)
        return self.from_asset_partitions({AssetPartition(asset_key, pk) for pk in partition_keys})

    def _partition_def_of(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.asset_graph.get_assets_def(asset_key).partitions_def

    def from_time_window(self, asset_key: AssetKey, time_window: TimeWindow) -> AssetSlice:
        partitions_def = check.not_none(self._partition_def_of(asset_key))
        check.inst(partitions_def, TimeWindowPartitionsDefinition)
        assert isinstance(partitions_def, TimeWindowPartitionsDefinition)
        return self._to_asset_slice(
            asset_key=asset_key,
            value=TimeWindowPartitionsSubset(
                partitions_def=partitions_def,
                num_partitions=None,
                included_time_windows=[time_window],
            ),
        )

    def complete_asset_slice(self, asset_key: AssetKey) -> AssetSlice:
        partitions_def = self.asset_graph.get_assets_def(asset_key).partitions_def
        valid_asset_subset = AssetSubset.all(
            asset_key=asset_key,
            partitions_def=partitions_def,
            dynamic_partitions_store=self.asset_graph_view.queryer,
            current_time=self.asset_graph_view.current_dt,
        ).as_valid(partitions_def)
        return AssetSlice(
            asset_graph_view=self.asset_graph_view,
            valid_asset_subset=valid_asset_subset,
        )

    def _to_asset_slice(
        self, asset_key: AssetKey, value: Union[bool, PartitionsSubset]
    ) -> AssetSlice:
        return AssetSlice(
            self.asset_graph_view,
            AssetSubset(asset_key, value).as_valid(
                self.asset_graph.get_assets_def(asset_key).partitions_def
            ),
        )
