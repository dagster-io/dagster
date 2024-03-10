from datetime import datetime
from typing import TYPE_CHECKING, AbstractSet, Iterable, Mapping, NamedTuple, NewType, Optional

from dagster import _check as check
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
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
    and it impacts the behavior of partioning and partition mapping. For example, if an
    if you get the "last" partition window of a given partitions definition, it is with
    respect to the effective time.

    Last event id: Our event log has a monotonic increasing event id. This is used to
    cursor the event log. This event_id is also propogated to derived tables to indicate.
    This allows us to query the state of the event log at a given point in time.

    Note that insertion time of the last_event_id is not the same as the effective time.

    A last_event_id of None indicates that the reads will be volatile will immediately
    reflect any subsequent writes.
    """

    effective_dt: datetime
    last_event_id: Optional[int]


class _AssetSliceCompatibleSubset(ValidAssetSubset): ...


DEFAULT_PARTITION_KEY = "__default__"

PartitionKey = NewType("PartitionKey", str)
"""
PartitionKey is a string that represents a partition key. It is a new type so
that we can track the use of strs as partition keys.

PartitionKey should only be created via the static factory methods on AssetPartitionKey.
We want to consolidate all partition key creation so we have a leverage point to change
how they. Eventually we want to create a new singleton string partition to represent
the "all" partition key for unpartitioned assets.
"""


def _to_partiton_key(partition_key: Optional[str]) -> PartitionKey:
    return PartitionKey(partition_key) if partition_key else PartitionKey(DEFAULT_PARTITION_KEY)


def _to_asset_partition_key(ak_pk: AssetKeyPartitionKey) -> "AssetPartitionKey":
    return AssetPartitionKey(ak_pk.asset_key, _to_partiton_key(ak_pk.partition_key))


def _check_partition_key_str_set(
    partition_keys: AbstractSet[str], partitions_def: "PartitionsDefinition"
) -> AbstractSet[PartitionKey]:
    for partition_key in partition_keys:
        if not partitions_def.has_partition_key(partition_key):
            check.failed(f"Partition key {partition_key} not in partitions def {partitions_def}")
    return {PartitionKey(pk) for pk in partition_keys}


class AssetPartitionKey(NamedTuple):
    """Represents a a partition in a particular asset. Prefer usage to AssetKeyPartitionKey.
    If you need to convert AssetKeyPartitionKeys to AssetPartitionKeys, use the static
    factory methods.
    """

    asset_key: AssetKey
    partition_key: PartitionKey

    @staticmethod
    def partition_keys_from_asset_key_partition_keys(
        asset_key_partition_keys: Iterable[AssetKeyPartitionKey],
    ) -> AbstractSet["PartitionKey"]:
        return {
            PartitionKey(check.not_none(akpk.partition_key, "No None partition keys"))
            for akpk in asset_key_partition_keys
        }

    @staticmethod
    def from_str_partition_keys(
        asset_key: AssetKey, partition_keys: Iterable[str], partitions_def: "PartitionsDefinition"
    ) -> AbstractSet["AssetPartitionKey"]:
        return {AssetPartitionKey(asset_key, PartitionKey(pk)) for pk in partition_keys}

    @staticmethod
    def from_asset_key_partition_keys(
        asset_key_partition_keys: Iterable[AssetKeyPartitionKey],
    ) -> AbstractSet["AssetPartitionKey"]:
        return {_to_asset_partition_key(akpk) for akpk in asset_key_partition_keys}


def _slice_from_subset(asset_graph_view: "AssetGraphView", subset: AssetSubset) -> "AssetSlice":
    valid_subset = subset.as_valid(
        asset_graph_view.asset_graph.get(subset.asset_key).partitions_def
    )
    return AssetSlice(asset_graph_view, _AssetSliceCompatibleSubset(*valid_subset))


class AssetSlice:
    """An asset slice represents a set of partitions for a given asset key. It is
    tied to a particular instance of an AssetGraphView, and is read-only.

    With an asset slice you are able to traverse the set of partitions resident
    in an asset graph at any point in time.

    ```python
        asset_graph_view_t0 = AssetGraphView.for_test(defs, effective_dt=some_date())

        some_asset_slice = asset_graph_view_to.get_asset_slice(some_asset.key)

        for parent_slice in some_asset_slice.get_parent_slices().values():
            # do something with the parent slice
    ```

    AssetSlice is read-only and tied to a specific AssetGraphView. Therefore
    we can aggressively use cached methods and properties. However different methods
    have different performance characterics so we have the following conventions:

    Naming conventions
    * Properties guaranteed to be fast.
    * Methods prefixed with `get_` do some work in-memory but not hugely expensive.
    * Methods prefixed with `compute_` do potentially expensive work, like compute
      partition mappings and query the instance.

      We also use this prefix to indicate that they fully materialize partition sets
      These can potentially be very expensive if the underlying partition set has
      an in-memory representation that involves large time windows. I.e. if the
      underlying PartitionsSubset in the ValidAssetSubset is a
      TimeWindowPartitionsSubset Usage of these methods should be avoided if
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

    def compute_partition_keys(self) -> AbstractSet[PartitionKey]:
        if not self._compatible_subset.is_partitioned:
            return (
                {PartitionKey(DEFAULT_PARTITION_KEY)}
                if self._compatible_subset.bool_value
                else set()
            )
        else:
            return {
                PartitionKey(partition_key)
                for partition_key in self._compatible_subset.subset_value.get_partition_keys()
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

    def only_str_partition_keys(self, partition_keys: AbstractSet[str]) -> "AssetSlice":
        """Return a new AssetSlice with only the given partition keys if they are in the slice."""
        partitions_def = check.not_none(self._partitions_def, "Must have partitions def")
        return _slice_from_subset(
            self._asset_graph_view,
            self._compatible_subset
            & AssetSubset.from_partition_keys(
                asset_key=self.asset_key,
                partitions_def=partitions_def,
                partition_keys=_check_partition_key_str_set(partition_keys, partitions_def),
            ),
        )


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

        self._stale_resolver = stale_resolver
        # stale resolve has a CachingInstanceQueryer which has a DagsterInstance
        # so just passing the CachingStaleStatusResolver is enough
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
