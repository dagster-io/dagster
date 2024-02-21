import dataclasses
import datetime
import functools
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    FrozenSet,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

import pendulum

from dagster._core.definitions.asset_condition.asset_condition import (
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from ..asset_graph import AssetGraph
from ..asset_subset import AssetSubset, ValidAssetSubset

if TYPE_CHECKING:
    from ..asset_daemon_context import AssetDaemonContext
    from .asset_condition import (
        AssetCondition,
        AssetConditionEvaluation,
        AssetConditionEvaluationState,
        AssetSubsetWithMetadata,
    )

T = TypeVar("T")


def root_property(fn: Callable[[Any], T]) -> Callable[[Any], T]:
    """Ensures that a given property is always accessed via the root context, ensuring that any
    cached properties are accessed correctly.
    """

    def wrapped(self: Any) -> Any:
        return fn(self.root_context)

    return wrapped


@dataclass(frozen=True)
class AssetConditionEvaluationContext:
    """Context object containing methods and properties used for evaluating the entire state of an
    asset's automation rules.
    """

    asset_key: AssetKey
    condition: "AssetCondition"
    previous_evaluation_state: Optional["AssetConditionEvaluationState"]
    previous_evaluation: Optional["AssetConditionEvaluation"]
    candidate_subset: ValidAssetSubset

    instance_queryer: CachingInstanceQueryer
    data_time_resolver: CachingDataTimeResolver
    daemon_context: "AssetDaemonContext"

    evaluation_state_by_key: Mapping[AssetKey, "AssetConditionEvaluationState"]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]

    start_timestamp: float
    root_ref: Optional["AssetConditionEvaluationContext"] = None

    @staticmethod
    def create(
        asset_key: AssetKey,
        condition: "AssetCondition",
        previous_evaluation_state: Optional["AssetConditionEvaluationState"],
        instance_queryer: CachingInstanceQueryer,
        data_time_resolver: CachingDataTimeResolver,
        daemon_context: "AssetDaemonContext",
        evaluation_state_by_key: Mapping[AssetKey, "AssetConditionEvaluationState"],
        expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
    ) -> "AssetConditionEvaluationContext":
        partitions_def = instance_queryer.asset_graph.get_partitions_def(asset_key)

        return AssetConditionEvaluationContext(
            asset_key=asset_key,
            condition=condition,
            previous_evaluation_state=previous_evaluation_state,
            previous_evaluation=previous_evaluation_state.previous_evaluation
            if previous_evaluation_state
            else None,
            candidate_subset=AssetSubset.all(
                asset_key,
                partitions_def,
                instance_queryer,
                instance_queryer.evaluation_time,
            ),
            data_time_resolver=data_time_resolver,
            instance_queryer=instance_queryer,
            daemon_context=daemon_context,
            evaluation_state_by_key=evaluation_state_by_key,
            expected_data_time_mapping=expected_data_time_mapping,
            start_timestamp=pendulum.now("UTC").timestamp(),
        )

    def for_child(
        self, condition: "AssetCondition", candidate_subset: AssetSubset
    ) -> "AssetConditionEvaluationContext":
        return dataclasses.replace(
            self,
            condition=condition,
            previous_evaluation=self.previous_evaluation.for_child(condition)
            if self.previous_evaluation
            else None,
            candidate_subset=candidate_subset,
            root_ref=self.root_context,
            start_timestamp=pendulum.now("UTC").timestamp(),
        )

    @property
    def root_context(self) -> "AssetConditionEvaluationContext":
        """A reference to the context of the root condition for this evaluation."""
        return self.root_ref or self

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.asset_graph.get_partitions_def(self.asset_key)

    @property
    def evaluation_time(self) -> datetime.datetime:
        """Returns the time at which this rule is being evaluated."""
        return self.instance_queryer.evaluation_time

    @property
    def previous_max_storage_id(self) -> Optional[int]:
        return (
            self.previous_evaluation_state.max_storage_id
            if self.previous_evaluation_state
            else None
        )

    @property
    def previous_evaluation_timestamp(self) -> Optional[float]:
        return (
            self.previous_evaluation_state.previous_tick_evaluation_timestamp
            if self.previous_evaluation_state
            else None
        )

    @property
    def previous_true_subset(self) -> AssetSubset:
        if self.previous_evaluation is None:
            return self.empty_subset()
        return self.previous_evaluation.true_subset

    @property
    def previous_candidate_subset(self) -> AssetSubset:
        if self.previous_evaluation is None:
            return self.empty_subset()
        candidate_subset = self.previous_evaluation.candidate_subset
        if isinstance(candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return AssetSubset.all(
                self.asset_key, self.partitions_def, self.instance_queryer, self.evaluation_time
            )
        else:
            return candidate_subset

    @property
    def previous_subsets_with_metadata(self) -> Sequence["AssetSubsetWithMetadata"]:
        if self.previous_evaluation is None:
            return []
        return self.previous_evaluation.subsets_with_metadata

    @functools.cached_property
    @root_property
    def parent_will_update_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions whose parents will be updated on this tick, and which
        can be materialized in the same run as this asset.
        """
        subset = self.empty_subset()
        for parent_key in self.asset_graph.get_parents(self.asset_key):
            if not self.materializable_in_same_run(self.asset_key, parent_key):
                continue
            parent_info = self.evaluation_state_by_key.get(parent_key)
            if not parent_info:
                continue
            parent_subset = parent_info.true_subset.as_valid(self.partitions_def)
            subset |= parent_subset._replace(asset_key=self.asset_key)
        return subset

    @functools.cached_property
    @root_property
    def materialized_since_previous_tick_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return AssetSubset.from_asset_partitions_set(
            self.asset_key,
            self.partitions_def,
            self.instance_queryer.get_asset_partitions_updated_after_cursor(
                self.asset_key,
                asset_partitions=None,
                after_cursor=self.previous_max_storage_id,
                respect_materialization_data_versions=False,
            ),
        )

    @property
    @root_property
    def previous_tick_requested_subset(self) -> AssetSubset:
        """The set of asset partitions that were requested (or discarded) on the previous tick."""
        if (
            self.previous_evaluation_state is None
            or self.previous_evaluation_state.previous_evaluation is None
        ):
            return self.empty_subset()

        return (
            self.previous_evaluation_state.previous_evaluation.get_requested_or_discarded_subset()
        )

    @property
    def materialized_requested_or_discarded_since_previous_tick_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return self.materialized_since_previous_tick_subset | self.previous_tick_requested_subset

    @functools.cached_property
    @root_property
    def _parent_has_updated_subset_and_new_latest_storage_id(
        self,
    ) -> Tuple[ValidAssetSubset, Optional[int]]:
        """Returns the set of asset partitions whose parents have updated since the last time this
        condition was evaluated.
        """
        (
            asset_partitions,
            cursor,
        ) = self.root_context.instance_queryer.asset_partitions_with_newly_updated_parents_and_new_cursor(
            latest_storage_id=self.previous_max_storage_id,
            child_asset_key=self.root_context.asset_key,
            map_old_time_partitions=False,
        )
        return AssetSubset.from_asset_partitions_set(
            self.asset_key, self.partitions_def, asset_partitions
        ), cursor

    @property
    @root_property
    def parent_has_updated_subset(self) -> ValidAssetSubset:
        subset, _ = self._parent_has_updated_subset_and_new_latest_storage_id
        return subset

    @property
    @root_property
    def new_max_storage_id(self) -> Optional[int]:
        _, storage_id = self._parent_has_updated_subset_and_new_latest_storage_id
        return storage_id

    @property
    def parent_has_or_will_update_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions whose parents have updated since the last time this
        condition was evaluated, or will update on this tick.
        """
        return self.parent_has_updated_subset | self.root_context.parent_will_update_subset

    @property
    def candidate_parent_has_or_will_update_subset(self) -> ValidAssetSubset:
        """Returns the set of candidates for this tick which have parents that have updated since
        the previous tick, or will update on this tick.
        """
        return self.candidate_subset & self.parent_has_or_will_update_subset

    @property
    def candidates_not_evaluated_on_previous_tick_subset(self) -> ValidAssetSubset:
        """Returns the set of candidates for this tick which were not candidates on the previous
        tick.
        """
        from .asset_condition import HistoricalAllPartitionsSubsetSentinel

        if not self.previous_evaluation:
            return self.candidate_subset
        # when the candidate_subset is HistoricalAllPartitionsSubsetSentinel, this indicates that the
        # entire asset was evaluated for this condition on the previous tick, and so no candidates
        # were *not* evaluated on the previous tick
        elif isinstance(
            self.previous_evaluation.candidate_subset, HistoricalAllPartitionsSubsetSentinel
        ):
            return self.empty_subset()
        return self.candidate_subset - self.previous_evaluation.candidate_subset

    def materializable_in_same_run(self, child_key: AssetKey, parent_key: AssetKey) -> bool:
        """Returns whether a child asset can be materialized in the same run as a parent asset."""
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        return (
            # both assets must be materializable
            child_key in self.asset_graph.materializable_asset_keys
            and parent_key in self.asset_graph.materializable_asset_keys
            # the parent must have the same partitioning
            and self.asset_graph.have_same_partitioning(child_key, parent_key)
            # the parent must have a simple partition mapping to the child
            and (
                not self.asset_graph.is_partitioned(parent_key)
                or isinstance(
                    self.asset_graph.get_partition_mapping(child_key, parent_key),
                    (TimeWindowPartitionMapping, IdentityPartitionMapping),
                )
            )
            # the parent must be in the same repository to be materialized alongside the candidate
            and (
                not isinstance(self.asset_graph, ExternalAssetGraph)
                or self.asset_graph.get_repository_handle(child_key)
                == self.asset_graph.get_repository_handle(parent_key)
            )
        )

    def get_parents_that_will_not_be_materialized_on_current_tick(
        self, *, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of parent asset partitions that will not be updated in the same run of
        this asset partition if a run is launched for this asset partition on this tick.
        """
        return {
            parent
            for parent in self.asset_graph.get_parents_partitions(
                dynamic_partitions_store=self.instance_queryer,
                current_time=self.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions
            if not self.will_update_asset_partition(parent)
            or not self.materializable_in_same_run(asset_partition.asset_key, parent.asset_key)
        }

    def will_update_asset_partition(self, asset_partition: AssetKeyPartitionKey) -> bool:
        parent_evaluation_state = self.evaluation_state_by_key.get(asset_partition.asset_key)
        if not parent_evaluation_state:
            return False
        return asset_partition in parent_evaluation_state.true_subset

    def add_evaluation_data_from_previous_tick(
        self,
        asset_partitions_by_frozen_metadata: Mapping[
            FrozenSet[Tuple[str, MetadataValue]], AbstractSet[AssetKeyPartitionKey]
        ],
        ignore_subset: AssetSubset,
    ) -> Tuple[AssetSubset, Sequence["AssetSubsetWithMetadata"]]:
        """Combines information calculated on this tick with information from the previous tick,
        returning a tuple of the combined true subset and the combined subsets with metadata.

        Args:
            asset_partitions_by_frozen_metadata: A mapping from metadata to the set of asset
                partitions that the rule applies to.
            ignore_subset: An AssetSubset which represents information that we should *not* carry
                forward from the previous tick.
        """
        from .asset_condition import AssetSubsetWithMetadata

        mapping = defaultdict(lambda: self.empty_subset())
        has_new_metadata_subset = self.empty_subset()
        for frozen_metadata, asset_partitions in asset_partitions_by_frozen_metadata.items():
            mapping[frozen_metadata] = AssetSubset.from_asset_partitions_set(
                self.asset_key, self.partitions_def, asset_partitions
            )
            has_new_metadata_subset |= mapping[frozen_metadata]

        # don't use information from the previous tick if we have explicit metadata for it or
        # we've explicitly said to ignore it
        ignore_subset = has_new_metadata_subset | ignore_subset

        for elt in self.previous_subsets_with_metadata:
            carry_forward_subset = elt.subset.as_valid(self.partitions_def) - ignore_subset
            if carry_forward_subset.size > 0:
                mapping[elt.frozen_metadata] |= carry_forward_subset

        # for now, an asset is in the "true" subset if and only if we have some metadata for it
        true_subset = self.empty_subset()
        for subset in mapping.values():
            true_subset |= subset

        return (
            self.candidate_subset & true_subset,
            [
                AssetSubsetWithMetadata(subset, dict(metadata))
                for metadata, subset in mapping.items()
            ],
        )

    def empty_subset(self) -> ValidAssetSubset:
        return AssetSubset.empty(self.asset_key, self.partitions_def)
