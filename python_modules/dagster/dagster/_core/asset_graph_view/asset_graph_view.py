from datetime import datetime, timedelta
from typing import TYPE_CHECKING, AbstractSet, Dict, NamedTuple, Optional, Type, TypeVar

from dagster import _check as check
from dagster._core.asset_graph_view.entity_subset import EntitySubset, _ValidatedEntitySubsetValue
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey, T_EntityKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
    PartitionDimensionDefinition,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    get_time_partitions_def,
)
from dagster._core.loader import LoadingContext
from dagster._time import get_current_datetime
from dagster._utils.aiodataloader import DataLoader
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph, BaseAssetNode
    from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
        ValidAssetSubset,
    )
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.partition import PartitionsDefinition
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

U_EntityKey = TypeVar("U_EntityKey", AssetKey, AssetCheckKey, EntityKey)


class TemporalContext(NamedTuple):
    """TemporalContext represents an effective time, used for business logic, and last_event_id
    which is used to identify that state of the event log at some point in time. Put another way,
    the value of a TemporalContext represents a point in time and a snapshot of the event log.

    Effective time: This is the effective time of the computation in terms of business logic,
    and it impacts the behavior of partitioning and partition mapping. For example,
    the "last" partition window of a given partitions definition, it is with
    respect to the effective time.

    Last event id: Our event log has a monotonically increasing event id. This is used to
    cursor the event log. This event_id is also propogated to derived tables to indicate
    when that record is valid.  This allows us to query the state of the event log
    at a given point in time.

    Note that insertion time of the last_event_id is not the same as the effective time.

    A last_event_id of None indicates that the reads will be volatile will immediately
    reflect any subsequent writes.
    """

    effective_dt: datetime
    last_event_id: Optional[int]


class AssetGraphView(LoadingContext):
    """The Asset Graph View. It is a view of the asset graph from the perspective of a specific
    temporal context.

    If the user wants to get a new view of the asset graph with a new effective date or last event
    id, they should create a new instance of an AssetGraphView. If they do not they will get
    incorrect results because the AssetGraphView and its associated classes (like EntitySubset)
    cache results based on the effective date and last event id.

    ```python
        # in a test case
        asset_graph_view_t0 = AssetGraphView.for_test(defs, effective_dt=some_date())

        #
        # call materialize on an asset in defs
        #
        # must create a new AssetGraphView to get the correct results,
        # asset_graph_view_t1 will not reflect the new materialization
        asset_graph_view_t1 = AssetGraphView.for_test(defs, effective_dt=some_date())
    ```

    """

    @staticmethod
    def for_test(
        defs: "Definitions",
        instance: Optional["DagsterInstance"] = None,
        effective_dt: Optional[datetime] = None,
        last_event_id: Optional[int] = None,
    ):
        from dagster._core.instance import DagsterInstance

        instance = instance or DagsterInstance.ephemeral()
        return AssetGraphView(
            temporal_context=TemporalContext(
                effective_dt=effective_dt or get_current_datetime(),
                last_event_id=last_event_id or instance.event_log_storage.get_maximum_record_id(),
            ),
            instance=instance,
            asset_graph=defs.get_asset_graph(),
        )

    def __init__(
        self,
        *,
        temporal_context: TemporalContext,
        instance: "DagsterInstance",
        asset_graph: "BaseAssetGraph",
    ):
        from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

        self._temporal_context = temporal_context
        self._instance = instance
        self._loaders = {}
        self._asset_graph = asset_graph

        self._queryer = CachingInstanceQueryer(
            instance=instance,
            asset_graph=asset_graph,
            loading_context=self,
            evaluation_time=temporal_context.effective_dt,
        )

    @property
    def instance(self) -> "DagsterInstance":
        return self._instance

    @property
    def loaders(self) -> Dict[Type, DataLoader]:
        return self._loaders

    @property
    def effective_dt(self) -> datetime:
        return self._temporal_context.effective_dt

    @property
    def last_event_id(self) -> Optional[int]:
        return self._temporal_context.last_event_id

    @property
    def asset_graph(self) -> "BaseAssetGraph[BaseAssetNode]":
        return self._asset_graph

    # In our transitional period there are lots of code path that take
    # a AssetGraphView and then call methods on the queryer. This is
    # formal accesor to we can do this legally, instead of using noqa accesses
    # of a private proeprty
    def get_inner_queryer_for_back_compat(self) -> "CachingInstanceQueryer":
        return self._queryer

    def _get_partitions_def(self, key: T_EntityKey) -> Optional["PartitionsDefinition"]:
        if isinstance(key, AssetKey):
            return self.asset_graph.get(key).partitions_def
        else:
            return None

    @cached_method
    def get_full_subset(self, *, key: T_EntityKey) -> EntitySubset[T_EntityKey]:
        partitions_def = self._get_partitions_def(key)
        value = (
            AllPartitionsSubset(
                partitions_def=partitions_def,
                dynamic_partitions_store=self._queryer,
                current_time=self.effective_dt,
            )
            if partitions_def
            else True
        )
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    @cached_method
    def get_empty_subset(self, *, key: T_EntityKey) -> EntitySubset[T_EntityKey]:
        partitions_def = self._get_partitions_def(key)
        value = partitions_def.empty_subset() if partitions_def else False
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    def get_subset_from_serializable_subset(
        self, serializable_subset: SerializableEntitySubset[T_EntityKey]
    ) -> Optional[EntitySubset[T_EntityKey]]:
        if serializable_subset.is_compatible_with_partitions_def(
            self._get_partitions_def(serializable_subset.key)
        ):
            return EntitySubset(
                self,
                key=serializable_subset.key,
                value=_ValidatedEntitySubsetValue(serializable_subset.value),
            )
        else:
            return None

    def legacy_get_asset_subset_from_valid_subset(
        self, subset: "ValidAssetSubset"
    ) -> EntitySubset[AssetKey]:
        return EntitySubset(self, key=subset.key, value=_ValidatedEntitySubsetValue(subset.value))

    def get_asset_subset_from_asset_partitions(
        self, key: AssetKey, asset_partitions: AbstractSet[AssetKeyPartitionKey]
    ) -> EntitySubset[AssetKey]:
        check.invariant(
            all(akpk.asset_key == key for akpk in asset_partitions),
            "All asset partitions must match input asset key.",
        )
        partition_keys = {
            akpk.partition_key for akpk in asset_partitions if akpk.partition_key is not None
        }
        partitions_def = self._get_partitions_def(key)
        value = (
            partitions_def.subset_with_partition_keys(partition_keys)
            if partitions_def
            else bool(asset_partitions)
        )
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    def compute_parent_subset(
        self, parent_key: AssetKey, subset: EntitySubset[T_EntityKey]
    ) -> EntitySubset[AssetKey]:
        check.invariant(
            parent_key in self.asset_graph.get(subset.key).parent_entity_keys,
        )
        return self.compute_mapped_subset(parent_key, subset)

    def compute_child_subset(
        self, child_key: T_EntityKey, subset: EntitySubset[U_EntityKey]
    ) -> EntitySubset[T_EntityKey]:
        check.invariant(
            child_key in self.asset_graph.get(subset.key).child_entity_keys,
        )
        return self.compute_mapped_subset(child_key, subset)

    def compute_mapped_subset(
        self, to_key: T_EntityKey, from_subset: EntitySubset
    ) -> EntitySubset[T_EntityKey]:
        from_key = from_subset.key
        from_partitions_def = self.asset_graph.get(from_key).partitions_def
        to_partitions_def = self.asset_graph.get(to_key).partitions_def

        partition_mapping = self.asset_graph.get_partition_mapping(from_key, to_key)

        if from_key in self.asset_graph.get(to_key).parent_entity_keys:
            if from_partitions_def is None or to_partitions_def is None:
                return (
                    self.get_empty_subset(key=to_key)
                    if from_subset.is_empty
                    else self.get_full_subset(key=to_key)
                )
            to_partitions_subset = partition_mapping.get_downstream_partitions_for_partitions(
                upstream_partitions_subset=from_subset.get_internal_subset_value(),
                upstream_partitions_def=from_partitions_def,
                downstream_partitions_def=to_partitions_def,
                dynamic_partitions_store=self._queryer,
                current_time=self.effective_dt,
            )
        else:
            if to_partitions_def is None or from_subset.is_empty:
                return (
                    self.get_empty_subset(key=to_key)
                    if from_subset.is_empty
                    else self.get_full_subset(key=to_key)
                )
            to_partitions_subset = (
                partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
                    downstream_partitions_subset=from_subset.get_internal_subset_value()
                    if from_partitions_def is not None
                    else None,
                    downstream_partitions_def=from_partitions_def,
                    upstream_partitions_def=to_partitions_def,
                    dynamic_partitions_store=self._queryer,
                    current_time=self.effective_dt,
                ).partitions_subset
            )

        return EntitySubset(
            self,
            key=to_key,
            value=_ValidatedEntitySubsetValue(to_partitions_subset),
        )

    def compute_intersection_with_partition_keys(
        self, partition_keys: AbstractSet[str], asset_subset: EntitySubset[AssetKey]
    ) -> EntitySubset[AssetKey]:
        """Return a new EntitySubset with only the given partition keys if they are in the subset."""
        if not partition_keys:
            return self.get_empty_subset(key=asset_subset.key)

        partitions_def = check.not_none(
            self._get_partitions_def(asset_subset.key), "Must have partitions def"
        )
        for partition_key in partition_keys:
            if not partitions_def.has_partition_key(
                partition_key,
                current_time=self.effective_dt,
                dynamic_partitions_store=self._queryer,
            ):
                check.failed(
                    f"Partition key {partition_key} not in partitions def {partitions_def}"
                )

        keys_subset = self.get_asset_subset_from_asset_partitions(
            asset_subset.key, {AssetKeyPartitionKey(asset_subset.key, pk) for pk in partition_keys}
        )
        return asset_subset.compute_intersection(keys_subset)

    def compute_latest_time_window_subset(
        self, asset_key: AssetKey, lookback_delta: Optional[timedelta] = None
    ) -> EntitySubset[AssetKey]:
        """Compute the subset of the asset which exists within the latest time partition window. If
        the asset has no time dimension, this will always return the full subset. If
        lookback_delta is provided, all partitions that are up to that timedelta before the
        end of the latest time partition window will be included.
        """
        partitions_def = self._get_partitions_def(asset_key)
        time_partitions_def = get_time_partitions_def(partitions_def)
        if time_partitions_def is None:
            # if the asset has no time dimension, then return a full subset
            return self.get_full_subset(key=asset_key)

        latest_time_window = time_partitions_def.get_last_partition_window(self.effective_dt)
        if latest_time_window is None:
            return self.get_empty_subset(key=asset_key)

        # the time window in which to look for partitions
        time_window = (
            TimeWindow(
                start=max(
                    # do not look before the start of the definition
                    time_partitions_def.start,
                    latest_time_window.end - lookback_delta,
                ),
                end=latest_time_window.end,
            )
            if lookback_delta
            else latest_time_window
        )

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            return self._build_time_partition_subset(asset_key, partitions_def, time_window)
        elif isinstance(partitions_def, MultiPartitionsDefinition):
            return self._build_multi_partition_subset(
                asset_key, self._get_multi_dim_info(asset_key), time_window
            )
        else:
            check.failed(f"Unsupported partitions_def: {partitions_def}")

    def compute_missing_subset(
        self, asset_key: "AssetKey", from_subset: EntitySubset[AssetKey]
    ) -> EntitySubset[AssetKey]:
        """Returns a subset which is the subset of the input subset that has never been materialized
        (if it is a materializable asset) or observered (if it is an observable asset).
        """
        # TODO: this logic should be simplified once we have a unified way of detecting both
        # materializations and observations through the parittion status cache. at that point, the
        # definition will slightly change to search for materializations and observations regardless
        # of the materializability of the asset
        if self.asset_graph.get(asset_key).is_materializable:
            # cheap call which takes advantage of the partition status cache
            materialized_subset = self._queryer.get_materialized_asset_subset(asset_key=asset_key)
            materialized_subset = EntitySubset(
                self, key=asset_key, value=_ValidatedEntitySubsetValue(materialized_subset.value)
            )
            return from_subset.compute_difference(materialized_subset)
        else:
            # more expensive call
            missing_asset_partitions = {
                ap
                for ap in from_subset.expensively_compute_asset_partitions()
                if not self._queryer.asset_partition_has_materialization_or_observation(ap)
            }
            return self.get_asset_subset_from_asset_partitions(
                key=asset_key, asset_partitions=missing_asset_partitions
            )

    @cached_method
    def compute_in_progress_asset_subset(self, *, asset_key: AssetKey) -> EntitySubset[AssetKey]:
        # part of in progress run
        value = self._queryer.get_in_progress_asset_subset(asset_key=asset_key).value
        return EntitySubset(self, key=asset_key, value=_ValidatedEntitySubsetValue(value))

    @cached_method
    def compute_failed_asset_subset(self, *, asset_key: "AssetKey") -> EntitySubset[AssetKey]:
        value = self._queryer.get_failed_asset_subset(asset_key=asset_key).value
        return EntitySubset(self, key=asset_key, value=_ValidatedEntitySubsetValue(value))

    @cached_method
    def compute_updated_since_cursor_subset(
        self, *, asset_key: AssetKey, cursor: Optional[int]
    ) -> EntitySubset[AssetKey]:
        value = self._queryer.get_asset_subset_updated_after_cursor(
            asset_key=asset_key, after_cursor=cursor
        ).value
        return EntitySubset(self, key=asset_key, value=_ValidatedEntitySubsetValue(value))

    class MultiDimInfo(NamedTuple):
        tw_dim: PartitionDimensionDefinition
        secondary_dim: PartitionDimensionDefinition

        @property
        def tw_partition_def(self) -> TimeWindowPartitionsDefinition:
            return check.inst(
                self.tw_dim.partitions_def,
                TimeWindowPartitionsDefinition,
            )

        @property
        def secondary_partition_def(self) -> "PartitionsDefinition":
            return self.secondary_dim.partitions_def

    def _get_multi_dim_info(self, asset_key: AssetKey) -> "MultiDimInfo":
        partitions_def = check.inst(
            self._get_partitions_def(asset_key),
            MultiPartitionsDefinition,
        )
        return self.MultiDimInfo(
            tw_dim=partitions_def.time_window_dimension,
            secondary_dim=partitions_def.secondary_dimension,
        )

    def _build_time_partition_subset(
        self,
        asset_key: AssetKey,
        partitions_def: TimeWindowPartitionsDefinition,
        time_window: TimeWindow,
    ) -> EntitySubset[AssetKey]:
        return self.get_full_subset(key=asset_key).compute_intersection(
            self.get_asset_subset_from_asset_partitions(
                asset_key,
                {
                    AssetKeyPartitionKey(asset_key, pk)
                    for pk in partitions_def.get_partition_keys_in_time_window(time_window)
                },
            )
        )

    def _build_multi_partition_subset(
        self, asset_key: AssetKey, multi_dim_info: MultiDimInfo, time_window: TimeWindow
    ) -> EntitySubset[AssetKey]:
        # Note: Potential perf improvement here. There is no way to encode a cartesian product
        # in the underlying PartitionsSet. We could add a specialized PartitionsSubset
        # subclass that itself composed two PartitionsSubset to avoid materializing the entire
        # partitions range.
        return self.get_asset_subset_from_asset_partitions(
            asset_key,
            {
                AssetKeyPartitionKey(
                    asset_key,
                    MultiPartitionKey(
                        {
                            multi_dim_info.tw_dim.name: tw_pk,
                            multi_dim_info.secondary_dim.name: secondary_pk,
                        }
                    ),
                )
                for tw_pk in multi_dim_info.tw_partition_def.get_partition_keys_in_time_window(
                    time_window
                )
                for secondary_pk in multi_dim_info.secondary_partition_def.get_partition_keys(
                    current_time=self.effective_dt,
                    dynamic_partitions_store=self._queryer,
                )
            },
        )
