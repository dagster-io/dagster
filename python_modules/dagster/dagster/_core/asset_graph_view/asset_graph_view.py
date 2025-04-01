import functools
from collections.abc import Awaitable, Iterable
from datetime import datetime, timedelta
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Literal,
    NamedTuple,
    Optional,
    TypeVar,
)

from dagster import _check as check
from dagster._check import CheckError
from dagster._core.asset_graph_view.entity_subset import EntitySubset, _ValidatedEntitySubsetValue
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey, T_EntityKey
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
    PartitionDimensionDefinition,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.partition_mapping import UpstreamPartitionsResult
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
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
    from dagster._core.definitions.partition_key_range import PartitionKeyRange
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
    from dagster._core.storage.dagster_run import RunRecord
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
    def loaders(self) -> dict[type, DataLoader]:  # pyright: ignore[reportIncompatibleMethodOverride]
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

    def get_entity_subset_in_range(
        self, asset_key: AssetKey, partition_key_range: "PartitionKeyRange"
    ) -> EntitySubset[AssetKey]:
        partitions_def = check.not_none(
            self._get_partitions_def(asset_key), "Must have partitions def"
        )
        partition_subset_in_range = partitions_def.get_subset_in_range(
            partition_key_range=partition_key_range,
            dynamic_partitions_store=self._queryer,
        )
        return EntitySubset(
            self, key=asset_key, value=_ValidatedEntitySubsetValue(partition_subset_in_range)
        )

    def get_entity_subset_from_asset_graph_subset(
        self, asset_graph_subset: AssetGraphSubset, key: AssetKey
    ) -> EntitySubset[AssetKey]:
        check.invariant(
            self.asset_graph.has(key), f"Asset graph does not contain {key.to_user_string()}"
        )

        serializable_subset = self._with_current_partitions_def(
            asset_graph_subset.get_asset_subset(key, self.asset_graph)
        )

        return EntitySubset(
            self, key=key, value=_ValidatedEntitySubsetValue(serializable_subset.value)
        )

    def _with_current_partitions_def(
        self, serializable_subset: SerializableEntitySubset
    ) -> SerializableEntitySubset:
        """Used to transform a persisted SerializableEntitySubset (e.g. generated from backfill data)
        into an up-to-date one based on the latest partitions information in the asset graph. Raises
        an exception if the partitions in the asset graph are now totally incompatible (say, a
        partitioned asset is now unpartitioned, or the subset references keys that no longer exist)
        but adjusts the SerializableEntitySubset to reflect the latest version of the
        PartitionsDefinition if it differs but is still valid (for example, the range of the
        partitions have been extended and the subset is still valid.
        """
        current_partitions_def = self._get_partitions_def(serializable_subset.key)
        key = serializable_subset.key
        value = serializable_subset.value

        if serializable_subset.is_partitioned:
            check.invariant(
                current_partitions_def is not None,
                f"{key.to_user_string()} was partitioned when originally stored, but is no longer partitioned.",
            )
            if isinstance(value, AllPartitionsSubset):
                check.invariant(
                    value.partitions_def == current_partitions_def,
                    f"Partitions definition for {key.to_user_string()} has an AllPartitionsSubset and no longer matches the stored partitions definition",
                )
                return serializable_subset
            elif isinstance(value, TimeWindowPartitionsSubset):
                serialized_partitions_def = value.partitions_def
                if (
                    not isinstance(current_partitions_def, TimeWindowPartitionsDefinition)
                    or serialized_partitions_def.timezone != current_partitions_def.timezone
                    or serialized_partitions_def.fmt != current_partitions_def.fmt
                    or serialized_partitions_def.cron_schedule
                    != current_partitions_def.cron_schedule
                ):
                    raise CheckError(
                        f"Stored partitions definition for {key.to_user_string()} is no longer compatible with the latest partitions definition",
                    )
                missing_subset = value - current_partitions_def.subset_with_all_partitions(
                    self._temporal_context.effective_dt,
                    self._instance,
                )
                if not missing_subset.is_empty:
                    raise CheckError(
                        f"Stored partitions definition for {key.to_user_string()} includes partitions {missing_subset} that are no longer present",
                    )

                return SerializableEntitySubset(
                    key, value.with_partitions_def(current_partitions_def)
                )
            else:
                return serializable_subset
        else:
            check.invariant(
                current_partitions_def is None,
                f"{key.to_user_string()} was un-partitioned when originally stored, but is now partitioned.",
            )
            return serializable_subset

    def iterate_asset_subsets(
        self, asset_graph_subset: AssetGraphSubset
    ) -> Iterable[EntitySubset[AssetKey]]:
        """Returns an Iterable of EntitySubsets representing the subset of each asset that this
        AssetGraphSubset contains.
        """
        for asset_key in asset_graph_subset.asset_keys:
            yield self.get_entity_subset_from_asset_graph_subset(asset_graph_subset, asset_key)

    def get_subset_from_serializable_subset(
        self, serializable_subset: SerializableEntitySubset[T_EntityKey]
    ) -> Optional[EntitySubset[T_EntityKey]]:
        key = serializable_subset.key
        if self.asset_graph.has(key) and serializable_subset.is_compatible_with_partitions_def(
            self._get_partitions_def(key)
        ):
            return EntitySubset(
                self, key=key, value=_ValidatedEntitySubsetValue(serializable_subset.value)
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

    def compute_parent_subset_and_required_but_nonexistent_subset(
        self, parent_key, subset: EntitySubset[T_EntityKey]
    ) -> tuple[EntitySubset[AssetKey], EntitySubset[AssetKey]]:
        check.invariant(
            parent_key in self.asset_graph.get(subset.key).parent_entity_keys,
        )
        to_key = parent_key
        to_partitions_def = self.asset_graph.get(to_key).partitions_def

        if subset.is_empty:
            return self.get_empty_subset(key=parent_key), self.get_empty_subset(key=parent_key)
        elif to_partitions_def is None:
            return self.get_full_subset(key=to_key), self.get_empty_subset(key=parent_key)

        upstream_partition_result = self._compute_upstream_partitions_result(to_key, subset)

        parent_subset = EntitySubset(
            self,
            key=to_key,
            value=_ValidatedEntitySubsetValue(upstream_partition_result.partitions_subset),
        )

        required_but_nonexistent_subset = EntitySubset(
            self,
            key=to_key,
            value=_ValidatedEntitySubsetValue(
                upstream_partition_result.required_but_nonexistent_subset
            ),
        )

        return parent_subset, required_but_nonexistent_subset

    def compute_parent_subset(
        self, parent_key: AssetKey, subset: EntitySubset[T_EntityKey]
    ) -> EntitySubset[AssetKey]:
        check.invariant(
            parent_key in self.asset_graph.get(subset.key).parent_entity_keys,
        )
        return self.compute_mapped_subset(parent_key, subset, direction="up")

    def compute_child_subset(
        self, child_key: T_EntityKey, subset: EntitySubset[U_EntityKey]
    ) -> EntitySubset[T_EntityKey]:
        check.invariant(
            child_key in self.asset_graph.get(subset.key).child_entity_keys,
        )
        return self.compute_mapped_subset(child_key, subset, direction="down")

    def _compute_upstream_partitions_result(
        self, to_key: T_EntityKey, from_subset: EntitySubset
    ) -> UpstreamPartitionsResult:
        from_key = from_subset.key
        parent_key = to_key
        partition_mapping = self.asset_graph.get_partition_mapping(from_key, parent_key)
        from_partitions_def = self.asset_graph.get(from_key).partitions_def
        to_partitions_def = self.asset_graph.get(to_key).partitions_def

        return partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
            downstream_partitions_subset=from_subset.get_internal_subset_value()
            if from_partitions_def is not None
            else None,
            downstream_partitions_def=from_partitions_def,
            upstream_partitions_def=check.not_none(to_partitions_def),
            dynamic_partitions_store=self._queryer,
            current_time=self.effective_dt,
        )

    def compute_mapped_subset(
        self, to_key: T_EntityKey, from_subset: EntitySubset, direction: Literal["up", "down"]
    ) -> EntitySubset[T_EntityKey]:
        from_key = from_subset.key
        from_partitions_def = self.asset_graph.get(from_key).partitions_def
        to_partitions_def = self.asset_graph.get(to_key).partitions_def

        if direction == "down":
            if from_partitions_def is None or to_partitions_def is None:
                return (
                    self.get_empty_subset(key=to_key)
                    if from_subset.is_empty
                    else self.get_full_subset(key=to_key)
                )

            partition_mapping = self.asset_graph.get_partition_mapping(to_key, from_key)

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

            to_partitions_subset = self._compute_upstream_partitions_result(
                to_key, from_subset
            ).partitions_subset

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

    async def compute_subset_with_status(
        self, key: AssetCheckKey, status: Optional["AssetCheckExecutionResolvedStatus"]
    ):
        from dagster._core.storage.event_log.base import AssetCheckSummaryRecord

        """Returns the subset of an asset check that matches a given status."""
        summary = await AssetCheckSummaryRecord.gen(self, key)
        latest_record = summary.last_check_execution_record if summary else None
        resolved_status = (
            await latest_record.resolve_status(self)
            if latest_record and await latest_record.targets_latest_materialization(self)
            else None
        )
        if resolved_status == status:
            return self.get_full_subset(key=key)
        else:
            return self.get_empty_subset(key=key)

    async def _compute_run_in_progress_check_subset(
        self, key: AssetCheckKey
    ) -> EntitySubset[AssetCheckKey]:
        from dagster._core.storage.asset_check_execution_record import (
            AssetCheckExecutionResolvedStatus,
        )

        return await self.compute_subset_with_status(
            key, AssetCheckExecutionResolvedStatus.IN_PROGRESS
        )

    async def _compute_execution_failed_check_subset(
        self, key: AssetCheckKey
    ) -> EntitySubset[AssetCheckKey]:
        from dagster._core.storage.asset_check_execution_record import (
            AssetCheckExecutionResolvedStatus,
        )

        return await self.compute_subset_with_status(
            key, AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
        )

    async def _compute_missing_check_subset(
        self, key: AssetCheckKey
    ) -> EntitySubset[AssetCheckKey]:
        return await self.compute_subset_with_status(key, None)

    async def _compute_run_in_progress_asset_subset(self, key: AssetKey) -> EntitySubset[AssetKey]:
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        partitions_def = self._get_partitions_def(key)
        if partitions_def:
            cache_value = await AssetStatusCacheValue.gen(self, (key, partitions_def))
            return (
                cache_value.get_in_progress_subset(self, key, partitions_def)
                if cache_value
                else self.get_empty_subset(key=key)
            )
        value = self._queryer.get_in_progress_asset_subset(asset_key=key).value
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    async def _compute_backfill_in_progress_asset_subset(
        self, key: AssetKey
    ) -> EntitySubset[AssetKey]:
        value = (
            self._queryer.get_active_backfill_in_progress_asset_graph_subset()
            .get_asset_subset(asset_key=key, asset_graph=self.asset_graph)
            .value
        )
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    async def _compute_execution_failed_asset_subset(self, key: AssetKey) -> EntitySubset[AssetKey]:
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        partitions_def = self._get_partitions_def(key)
        if partitions_def:
            cache_value = await AssetStatusCacheValue.gen(self, (key, partitions_def))
            return (
                cache_value.get_failed_subset(self, key, partitions_def)
                if cache_value
                else self.get_empty_subset(key=key)
            )
        value = self._queryer.get_failed_asset_subset(asset_key=key).value
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    async def _compute_missing_asset_subset(
        self, key: AssetKey, from_subset: EntitySubset
    ) -> EntitySubset[AssetKey]:
        """Returns a subset which is the subset of the input subset that has never been materialized
        (if it is a materializable asset) or observered (if it is an observable asset).
        """
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        # TODO: this logic should be simplified once we have a unified way of detecting both
        # materializations and observations through the parittion status cache. at that point, the
        # definition will slightly change to search for materializations and observations regardless
        # of the materializability of the asset
        if self.asset_graph.get(key).is_materializable:
            # cheap call which takes advantage of the partition status cache
            partitions_def = self._get_partitions_def(key)
            if partitions_def:
                cache_value = await AssetStatusCacheValue.gen(self, (key, partitions_def))
                materialized_subset = (
                    cache_value.get_materialized_subset(self, key, partitions_def)
                    if cache_value
                    else self.get_empty_subset(key=key)
                )
            else:
                value = self._queryer.get_materialized_asset_subset(asset_key=key).value
                materialized_subset = EntitySubset(
                    self, key=key, value=_ValidatedEntitySubsetValue(value)
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
                key=key, asset_partitions=missing_asset_partitions
            )

    @cached_method
    async def compute_run_in_progress_subset(self, *, key: EntityKey) -> EntitySubset:
        return await _dispatch(
            key=key,
            check_method=self._compute_run_in_progress_check_subset,
            asset_method=self._compute_run_in_progress_asset_subset,
        )

    @cached_method
    async def compute_backfill_in_progress_subset(self, *, key: EntityKey) -> EntitySubset:
        async def get_empty_subset(key: EntityKey) -> EntitySubset:
            return self.get_empty_subset(key=key)

        return await _dispatch(
            key=key,
            # asset checks cannot currently be backfilled
            check_method=get_empty_subset,
            asset_method=self._compute_backfill_in_progress_asset_subset,
        )

    @cached_method
    async def compute_execution_failed_subset(self, *, key: EntityKey) -> EntitySubset:
        return await _dispatch(
            key=key,
            check_method=self._compute_execution_failed_check_subset,
            asset_method=self._compute_execution_failed_asset_subset,
        )

    @cached_method
    async def compute_missing_subset(
        self, *, key: EntityKey, from_subset: EntitySubset
    ) -> EntitySubset:
        return await _dispatch(
            key=key,
            check_method=self._compute_missing_check_subset,
            asset_method=functools.partial(
                self._compute_missing_asset_subset, from_subset=from_subset
            ),
        )

    async def _expensively_filter_entity_subset(
        self, subset: EntitySubset, filter_fn: Callable[[Optional[str]], Awaitable[bool]]
    ) -> EntitySubset:
        if subset.is_partitioned:
            return subset.compute_intersection_with_partition_keys(
                {pk for pk in subset.expensively_compute_partition_keys() if await filter_fn(pk)}
            )
        else:
            return (
                subset
                if not subset.is_empty and await filter_fn(None)
                else self.get_empty_subset(key=subset.key)
            )

    async def _compute_latest_check_run_matches(
        self,
        partition_key: Optional[str],
        query_key: AssetCheckKey,
        filter_fn: Callable[["RunRecord"], bool],
    ) -> bool:
        from dagster._core.storage.dagster_run import RunRecord
        from dagster._core.storage.event_log.base import AssetCheckSummaryRecord

        check.invariant(partition_key is None, "Partitioned checks not supported")
        summary = await AssetCheckSummaryRecord.gen(self, query_key)
        check_record = summary.last_check_execution_record if summary else None
        if check_record and check_record.event:
            run_record = await RunRecord.gen(self, check_record.event.run_id)
            return bool(run_record) and filter_fn(run_record)
        else:
            return False

    async def _compute_latest_asset_run_matches(
        self,
        partition_key: Optional[str],
        query_key: AssetKey,
        filter_fn: Callable[["RunRecord"], bool],
    ) -> bool:
        from dagster._core.storage.dagster_run import RunRecord
        from dagster._core.storage.event_log.base import AssetRecord

        asset_record = await AssetRecord.gen(self, query_key)
        if (
            asset_record
            and asset_record.asset_entry.last_materialization
            and asset_record.asset_entry.last_materialization.asset_materialization
            and asset_record.asset_entry.last_materialization.asset_materialization.partition
            == partition_key
        ):
            run_record = await RunRecord.gen(
                self, asset_record.asset_entry.last_materialization.run_id
            )
            return bool(run_record) and filter_fn(run_record)
        else:
            return False

    async def compute_latest_run_matches_subset(
        self, from_subset: EntitySubset, filter_fn: Callable[["RunRecord"], bool]
    ) -> EntitySubset:
        return await _dispatch(
            key=from_subset.key,
            check_method=lambda k: self._expensively_filter_entity_subset(
                from_subset,
                filter_fn=functools.partial(
                    self._compute_latest_check_run_matches, query_key=k, filter_fn=filter_fn
                ),
            ),
            asset_method=lambda k: self._expensively_filter_entity_subset(
                from_subset,
                filter_fn=functools.partial(
                    self._compute_latest_asset_run_matches, query_key=k, filter_fn=filter_fn
                ),
            ),
        )

    async def _compute_updated_since_cursor_subset(
        self, key: AssetKey, cursor: Optional[int], require_data_version_update: bool = False
    ) -> EntitySubset[AssetKey]:
        value = self._queryer.get_asset_subset_updated_after_cursor(
            asset_key=key,
            after_cursor=cursor,
            require_data_version_update=require_data_version_update,
        ).value
        return EntitySubset(self, key=key, value=_ValidatedEntitySubsetValue(value))

    async def _compute_updated_since_time_subset(
        self, key: AssetCheckKey, time: datetime
    ) -> EntitySubset[AssetCheckKey]:
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import AssetCheckSummaryRecord

        # intentionally left unimplemented for AssetKey, as this is a less performant query
        summary = await AssetCheckSummaryRecord.gen(self, key)
        record = summary.last_check_execution_record if summary else None
        if (
            record is None
            or record.event is None
            or record.event.dagster_event_type != DagsterEventType.ASSET_CHECK_EVALUATION
            or record.event.timestamp < time.timestamp()
        ):
            return self.get_empty_subset(key=key)
        else:
            return self.get_full_subset(key=key)

    @cached_method
    async def compute_updated_since_temporal_context_subset(
        self, *, key: EntityKey, temporal_context: TemporalContext
    ) -> EntitySubset:
        return await _dispatch(
            key=key,
            check_method=functools.partial(
                self._compute_updated_since_time_subset, time=temporal_context.effective_dt
            ),
            asset_method=functools.partial(
                self._compute_updated_since_cursor_subset, cursor=temporal_context.last_event_id
            ),
        )

    @cached_method
    async def compute_data_version_changed_since_temporal_context_subset(
        self, *, key: AssetKey, temporal_context: TemporalContext
    ) -> EntitySubset[AssetKey]:
        return await self._compute_updated_since_cursor_subset(
            key, cursor=temporal_context.last_event_id, require_data_version_update=True
        )

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


I_Dispatch = TypeVar("I_Dispatch")
O_Dispatch = TypeVar("O_Dispatch")


async def _dispatch(
    *,
    key: EntityKey,
    check_method: Callable[[AssetCheckKey], Awaitable[O_Dispatch]],
    asset_method: Callable[[AssetKey], Awaitable[O_Dispatch]],
) -> O_Dispatch:
    """Applies a method for either a check or an asset."""
    if isinstance(key, AssetCheckKey):
        return await check_method(key)
    else:
        return await asset_method(key)
