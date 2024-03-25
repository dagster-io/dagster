from datetime import datetime
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Mapping,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    cast,
)

from dagster import _check as check
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
    PartitionDimensionDefinition,
)
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    DefaultPartitionsSubset,
    DynamicPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import (
    PartitionKeysTimeWindowPartitionsSubset,
    TimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph, BaseAssetNode
    from dagster._core.definitions.data_version import CachingStaleStatusResolver
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.partition import PartitionsDefinition
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


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


# We reserve the right to constraints on the AssetSubset that we are going to use
# in AssetSlice internals. Adding a NewType enforces that we do that conversion
# in one spot (see _slice_from_subset)
_AssetSliceCompatibleSubset = NewType("_AssetSliceCompatibleSubset", ValidAssetSubset)


def _slice_from_subset(asset_graph_view: "AssetGraphView", subset: AssetSubset) -> "AssetSlice":
    valid_subset = subset.as_valid(
        asset_graph_view.asset_graph.get(subset.asset_key).partitions_def
    )
    return AssetSlice(asset_graph_view, _AssetSliceCompatibleSubset(valid_subset))


class AssetSlice:
    """An asset slice represents a set of partitions for a given asset key. It is
    tied to a particular instance of an AssetGraphView, and is read-only.

    With an asset slice you are able to traverse the set of partitions resident
    in an asset graph at any point in time.

    ```python
        asset_graph_view_t0 = AssetGraphView.for_test(defs, effective_dt=some_date())

        some_asset_slice = asset_graph_view_to.get_asset_slice(some_asset.key)

        for parent_slice in some_asset_slice.compute_parent_slices().values():
            # do something with the parent slice
    ```

    AssetSlice is read-only and tied to a specific AssetGraphView. Therefore
    we can safely use cached methods and properties at will. However different methods
    have different performance characterics so we have the following conventions:

    Naming conventions
    * Properties are guaranteed to be fast.
    * Methods prefixed with `get_` do some work in-memory but are not hugely expensive.
    * Methods prefixed with `compute_` do potentially expensive work, like compute
      partition mappings and query the instance.

      We also use this prefix to indicate that they fully materialize partition sets
      These can potentially be very expensive if the underlying partition set has
      an in-memory representation that involves large time windows. I.e. if the
      underlying PartitionsSubset in the ValidAssetSubset is a
      TimeWindowPartitionsSubset. Usage of these methods should be avoided if
      possible if you are potentially dealing with slices with large time-based
      partition windows.
    """

    def __init__(
        self, asset_graph_view: "AssetGraphView", compatible_subset: _AssetSliceCompatibleSubset
    ):
        self._asset_graph_view = asset_graph_view
        self._compatible_subset = compatible_subset

    def convert_to_valid_asset_subset(self) -> ValidAssetSubset:
        return self._compatible_subset

    # only works for partitioned assets for now
    def compute_partition_keys(self) -> AbstractSet[str]:
        return {
            check.not_none(akpk.partition_key, "No None partition keys")
            for akpk in self._compatible_subset.asset_partitions
        }

    @property
    def asset_key(self) -> AssetKey:
        return self._compatible_subset.asset_key

    @property
    def parent_keys(self) -> AbstractSet[AssetKey]:
        return self._asset_graph_view.asset_graph.get(self.asset_key).parent_keys

    @property
    def child_keys(self) -> AbstractSet[AssetKey]:
        return self._asset_graph_view.asset_graph.get(self.asset_key).child_keys

    @property
    def _partitions_def(self) -> Optional["PartitionsDefinition"]:
        return self._asset_graph_view.asset_graph.get(self.asset_key).partitions_def

    @cached_method
    def compute_parent_slice(self, parent_asset_key: AssetKey) -> "AssetSlice":
        return self._asset_graph_view.compute_parent_asset_slice(parent_asset_key, self)

    @cached_method
    def compute_child_slice(self, child_asset_key: AssetKey) -> "AssetSlice":
        return self._asset_graph_view.compute_child_asset_slice(child_asset_key, self)

    @cached_method
    def compute_parent_slices(self) -> Mapping[AssetKey, "AssetSlice"]:
        return {ak: self.compute_parent_slice(ak) for ak in self.parent_keys}

    @cached_method
    def compute_child_slices(self) -> Mapping[AssetKey, "AssetSlice"]:
        return {ak: self.compute_child_slice(ak) for ak in self.child_keys}

    def compute_intersection_with_partition_keys(
        self, partition_keys: AbstractSet[str]
    ) -> "AssetSlice":
        """Return a new AssetSlice with only the given partition keys if they are in the slice."""
        return self._asset_graph_view.compute_intersection_with_partition_keys(partition_keys, self)

    @property
    def time_windows(self) -> Sequence[TimeWindow]:
        """Get the time windows for the asset slice. Only supports explicitly time-windowed partitions for now."""
        tw_partitions_def = check.not_none(
            self._time_window_partitions_def_in_context(), "Must be time windowed."
        )

        if isinstance(self._compatible_subset.subset_value, TimeWindowPartitionsSubset):
            return self._compatible_subset.subset_value.included_time_windows
        elif isinstance(self._compatible_subset.subset_value, AllPartitionsSubset):
            last_tw = tw_partitions_def.get_last_partition_window(
                self._asset_graph_view.effective_dt
            )
            return [TimeWindow(datetime.min, last_tw.end)] if last_tw else []
        elif isinstance(self._compatible_subset.subset_value, DefaultPartitionsSubset):
            check.inst(
                self._partitions_def,
                MultiPartitionsDefinition,
                "Must be multi-partition if we got here.",
            )
            tw_partition_keys = set()
            for multi_partition_key in check.is_list(
                list(self._compatible_subset.subset_value.get_partition_keys()),
                MultiPartitionKey,
                "Keys must be multi partition keys.",
            ):
                tm_partition_key = next(iter(multi_partition_key.keys_by_dimension.values()))
                tw_partition_keys.add(tm_partition_key)

            subset_from_tw = tw_partitions_def.subset_with_partition_keys(tw_partition_keys)
            check.inst(
                subset_from_tw,
                (TimeWindowPartitionsSubset, PartitionKeysTimeWindowPartitionsSubset),
                "Must be time window subset.",
            )
            if isinstance(subset_from_tw, TimeWindowPartitionsSubset):
                return subset_from_tw.included_time_windows
            elif isinstance(subset_from_tw, PartitionKeysTimeWindowPartitionsSubset):
                return subset_from_tw.included_time_windows
            else:
                check.failed(
                    f"Unsupported subset value in generated subset {self._compatible_subset.subset_value} created by keys {tw_partition_keys}"
                )

        check.failed(f"Unsupported subset value: {self._compatible_subset.subset_value}")

    def _time_window_partitions_def_in_context(self) -> Optional[TimeWindowPartitionsDefinition]:
        pd = self._partitions_def
        if isinstance(pd, TimeWindowPartitionsDefinition):
            return pd
        if isinstance(pd, MultiPartitionsDefinition):
            return pd.time_window_partitions_def if pd.has_time_window_dimension else None
        return None

    @property
    def is_empty(self) -> bool:
        return self._compatible_subset.size == 0


class AssetGraphView:
    """The Asset Graph View. It is a view of the asset graph from the perspective of a specific
    temporal context.

    If the user wants to get a new view of the asset graph with a new effective date or last event
    id, they should create a new instance of an AssetGraphView. If they do not they will get
    incorrect results because the AssetGraphView and its associated classes (like AssetSlice)
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
        import pendulum

        from dagster._core.definitions.data_version import CachingStaleStatusResolver
        from dagster._core.instance import DagsterInstance

        stale_resolver = CachingStaleStatusResolver(
            instance=instance or DagsterInstance.ephemeral(),
            asset_graph=defs.get_asset_graph(),
        )
        check.invariant(stale_resolver.instance_queryer, "Ensure instance queryer is constructed")
        return AssetGraphView(
            stale_resolver=stale_resolver,
            temporal_context=TemporalContext(
                effective_dt=effective_dt or pendulum.now(),
                last_event_id=last_event_id,
            ),
        )

    def __init__(
        self,
        *,
        temporal_context: TemporalContext,
        stale_resolver: "CachingStaleStatusResolver",
    ):
        # Current these properties have the ability to be lazily constructed.
        # We instead are going to try to retain the invariant that they are
        # constructed upfront so that initialization time is well-understood
        # and deterministic. If there are cheap operations that do not
        # require these instances, we should move them to a different abstraction.

        # ensure it is already constructed rather than created on demand
        check.invariant(stale_resolver._instance_queryer)  # noqa: SLF001
        # ensure it is already constructed rather than created on demand
        check.invariant(stale_resolver._asset_graph)  # noqa: SLF001

        # stale resolver has a CachingInstanceQueryer which has a DagsterInstance
        # so just passing the CachingStaleStatusResolver is enough
        self._stale_resolver = stale_resolver
        self._temporal_context = temporal_context

    @property
    def effective_dt(self) -> datetime:
        return self._temporal_context.effective_dt

    @property
    def last_event_id(self) -> Optional[int]:
        return self._temporal_context.last_event_id

    @property
    def asset_graph(self) -> "BaseAssetGraph[BaseAssetNode]":
        return self._stale_resolver.asset_graph

    @property
    def _queryer(self) -> "CachingInstanceQueryer":
        return self._stale_resolver.instance_queryer

    def _get_partitions_def(self, asset_key: "AssetKey") -> Optional["PartitionsDefinition"]:
        return self.asset_graph.get(asset_key).partitions_def

    def get_asset_slice(self, asset_key: "AssetKey") -> "AssetSlice":
        # not compute_asset_slice because dynamic partitions store
        # is just passed to AssetSubset.all, not invoked
        return _slice_from_subset(
            self,
            AssetSubset.all(
                asset_key=asset_key,
                partitions_def=self._get_partitions_def(asset_key),
                dynamic_partitions_store=self._queryer,
                current_time=self.effective_dt,
            ),
        )

    def compute_parent_asset_slice(
        self, parent_asset_key: AssetKey, asset_slice: AssetSlice
    ) -> AssetSlice:
        return _slice_from_subset(
            self,
            self.asset_graph.get_parent_asset_subset(
                dynamic_partitions_store=self._queryer,
                parent_asset_key=parent_asset_key,
                child_asset_subset=asset_slice.convert_to_valid_asset_subset(),
                current_time=self.effective_dt,
            ),
        )

    def compute_child_asset_slice(
        self, child_asset_key: "AssetKey", asset_slice: AssetSlice
    ) -> "AssetSlice":
        return _slice_from_subset(
            self,
            self.asset_graph.get_child_asset_subset(
                dynamic_partitions_store=self._queryer,
                child_asset_key=child_asset_key,
                current_time=self.effective_dt,
                parent_asset_subset=asset_slice.convert_to_valid_asset_subset(),
            ),
        )

    def compute_intersection_with_partition_keys(
        self, partition_keys: AbstractSet[str], asset_slice: AssetSlice
    ) -> "AssetSlice":
        """Return a new AssetSlice with only the given partition keys if they are in the slice."""
        partitions_def = check.not_none(
            self._get_partitions_def(asset_slice.asset_key), "Must have partitions def"
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

        return _slice_from_subset(
            self,
            asset_slice.convert_to_valid_asset_subset()
            & AssetSubset.from_partition_keys(
                asset_slice.asset_key, partitions_def, partition_keys
            ),
        )

    def create_from_time_window(self, asset_key: AssetKey, time_window: TimeWindow) -> AssetSlice:
        return _slice_from_subset(
            self,
            AssetSubset(
                asset_key=asset_key,
                value=TimeWindowPartitionsSubset(
                    partitions_def=_required_tw_partitions_def(self._get_partitions_def(asset_key)),
                    num_partitions=None,
                    included_time_windows=[time_window],
                ),
            ),
        )

    def create_latest_time_window_slice(self, asset_key: AssetKey) -> AssetSlice:
        """If the underlying asset is time-window partitioned, this will return the latest complete
        time window relative to the effective date. For example if it is daily partitioned starting
        at midnight every day.  If the effective date is before the start of the partition definition, this will
        return the empty time window (where both start and end are datetime.max).

        If the underlying asset is unpartitioned or static partitioned and it is not empty,
        this will return a time window from the beginning of time to the effective date. If
        it is empty it will return the empty time window.

        TODO: add language for multi-dimensional partitioning when we support it
        TODO: add language for dynamic partitioning when we support it
        """
        partitions_def = self._get_partitions_def(asset_key)
        if partitions_def is None or isinstance(
            partitions_def, (DynamicPartitionsDefinition, StaticPartitionsDefinition)
        ):
            return self.get_asset_slice(asset_key)

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            time_window = partitions_def.get_last_partition_window(self.effective_dt)
            return (
                self.create_from_time_window(asset_key, time_window)
                if time_window
                else self.create_empty_slice(asset_key)
            )

        if isinstance(partitions_def, MultiPartitionsDefinition):
            if not partitions_def.has_time_window_dimension:
                return self.get_asset_slice(asset_key)

            multi_dim_info = self._get_multi_dim_info(asset_key)
            last_tw = multi_dim_info.tw_partition_def.get_last_partition_window(self.effective_dt)
            return (
                self._build_multi_partition_slice(asset_key, multi_dim_info, last_tw)
                if last_tw
                else self.create_empty_slice(asset_key)
            )

        # Need to handle dynamic partitioning
        check.failed(f"Unsupported partitions_def: {partitions_def}")

    def create_empty_slice(self, asset_key: AssetKey) -> AssetSlice:
        return _slice_from_subset(
            self,
            AssetSubset.empty(asset_key, self._get_partitions_def(asset_key)),
        )

    class MultiDimInfo(NamedTuple):
        tw_dim: PartitionDimensionDefinition
        secondary_dim: PartitionDimensionDefinition

        @property
        def tw_partition_def(self) -> TimeWindowPartitionsDefinition:
            return cast(
                TimeWindowPartitionsDefinition,
                check.inst(self.tw_dim.partitions_def, TimeWindowPartitionsDefinition),
            )

        @property
        def secondary_partition_def(self) -> "PartitionsDefinition":
            return self.secondary_dim.partitions_def

    def _get_multi_dim_info(self, asset_key: AssetKey) -> "MultiDimInfo":
        partitions_def = cast(
            MultiPartitionsDefinition,
            check.inst(self._get_partitions_def(asset_key), MultiPartitionsDefinition),
        )
        return self.MultiDimInfo(
            tw_dim=partitions_def.time_window_dimension,
            secondary_dim=partitions_def.secondary_dimension,
        )

    def _build_multi_partition_slice(
        self, asset_key: AssetKey, multi_dim_info: MultiDimInfo, last_tw: TimeWindow
    ) -> "AssetSlice":
        # Note: Potential perf improvement here. There is no way to encode a cartesian product
        # in the underlying PartitionsSet. We could add a specialized PartitionsSubset
        # subclass that itself composed two PartitionsSubset to avoid materializing the entire
        # partitions range.
        return self.get_asset_slice(asset_key).compute_intersection_with_partition_keys(
            {
                MultiPartitionKey(
                    {
                        multi_dim_info.tw_dim.name: tw_pk,
                        multi_dim_info.secondary_dim.name: secondary_pk,
                    }
                )
                for tw_pk in multi_dim_info.tw_partition_def.get_partition_keys_in_time_window(
                    last_tw
                )
                for secondary_pk in multi_dim_info.secondary_partition_def.get_partition_keys(
                    current_time=self.effective_dt,
                    dynamic_partitions_store=self._queryer,
                )
            }
        )


def _required_tw_partitions_def(
    partitions_def: Optional["PartitionsDefinition"],
) -> TimeWindowPartitionsDefinition:
    return cast(
        TimeWindowPartitionsDefinition,
        check.inst(partitions_def, TimeWindowPartitionsDefinition, "Must be time windowed."),
    )
