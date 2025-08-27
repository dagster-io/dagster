import dataclasses
import datetime
import functools
import logging
import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Optional, TypeVar  # noqa: UP035

import dagster._check as check
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
    ValidAssetSubset,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionCursor,
    AutomationConditionNodeCursor,
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._time import get_current_timestamp

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
    from dagster._core.definitions.data_time import CachingDataTimeResolver
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )
    from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
        AutomationConditionEvaluator,
    )
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

T = TypeVar("T")


def root_property(fn: Callable[[Any], T]) -> Callable[[Any], T]:
    """Ensures that a given property is always accessed via the root context, ensuring that any
    cached properties are accessed correctly.
    """

    def wrapped(self: Any) -> Any:
        return fn(self.root_context)

    return wrapped


@dataclass(frozen=True)
class LegacyRuleEvaluationContext:
    """Context object containing methods and properties used for evaluating the entire state of an
    asset's automation rules.
    """

    asset_key: AssetKey
    condition: "AutomationCondition"
    cursor: Optional[AutomationConditionCursor]
    node_cursor: Optional[AutomationConditionNodeCursor]
    candidate_subset: ValidAssetSubset

    instance_queryer: "CachingInstanceQueryer"
    data_time_resolver: "CachingDataTimeResolver"

    request_subsets_by_key: Mapping[EntityKey, EntitySubset]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]

    start_timestamp: float
    respect_materialization_data_versions: bool
    auto_materialize_run_tags: Mapping[str, str]
    logger: logging.Logger
    root_ref: Optional["LegacyRuleEvaluationContext"] = None

    @staticmethod
    def create(asset_key: AssetKey, evaluator: "AutomationConditionEvaluator"):
        instance_queryer = evaluator.asset_graph_view.get_inner_queryer_for_back_compat()

        cursor = evaluator.cursor.get_previous_condition_cursor(asset_key)
        condition = check.not_none(evaluator.asset_graph.get(asset_key).automation_condition)
        partitions_def = evaluator.asset_graph.get(asset_key).partitions_def

        return LegacyRuleEvaluationContext(
            asset_key=asset_key,
            condition=condition,
            cursor=cursor,
            node_cursor=cursor.node_cursors_by_unique_id.get(
                condition.get_node_unique_id(parent_unique_id=None, index=0)
            )
            if cursor
            else None,
            candidate_subset=ValidAssetSubset.all(asset_key, partitions_def),
            data_time_resolver=evaluator.legacy_data_time_resolver,
            instance_queryer=instance_queryer,
            request_subsets_by_key=evaluator.request_subsets_by_key,
            expected_data_time_mapping=evaluator.legacy_expected_data_time_by_key,
            start_timestamp=get_current_timestamp(),
            respect_materialization_data_versions=evaluator.legacy_respect_materialization_data_versions,
            auto_materialize_run_tags=evaluator.legacy_auto_materialize_run_tags,
            logger=evaluator.logger,
        )

    def for_child(
        self,
        child_condition: "AutomationCondition",
        child_unique_id: str,
        candidate_subset: EntitySubset,
    ) -> "LegacyRuleEvaluationContext":
        return dataclasses.replace(
            self,
            condition=child_condition,
            node_cursor=self.cursor.node_cursors_by_unique_id.get(child_unique_id)
            if self.cursor
            else None,
            candidate_subset=ValidAssetSubset(
                key=candidate_subset.key, value=candidate_subset.get_internal_value()
            ),
            root_ref=self.root_context,
            start_timestamp=get_current_timestamp(),
        )

    @property
    def root_context(self) -> "LegacyRuleEvaluationContext":
        """A reference to the context of the root condition for this evaluation."""
        return self.root_ref or self

    @property
    def asset_graph(self) -> "BaseAssetGraph":
        return self.instance_queryer.asset_graph

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.asset_graph.get(self.asset_key).partitions_def

    @property
    def evaluation_time(self) -> datetime.datetime:
        """Returns the time at which this rule is being evaluated."""
        return self.instance_queryer.evaluation_time

    @property
    def previous_max_storage_id(self) -> Optional[int]:
        return self.cursor.temporal_context.last_event_id if self.cursor else None

    @property
    def previous_evaluation_timestamp(self) -> Optional[float]:
        return self.cursor.effective_timestamp if self.cursor else None

    @property
    def previous_true_subset(self) -> SerializableEntitySubset:
        if self.node_cursor is None:
            return self.empty_subset()
        return self.node_cursor.true_subset

    @property
    def previous_candidate_subset(self) -> SerializableEntitySubset:
        if self.node_cursor is None:
            return self.empty_subset()
        candidate_subset = self.node_cursor.candidate_subset
        if isinstance(candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return ValidAssetSubset.all(self.asset_key, self.partitions_def)
        else:
            return candidate_subset

    @property
    def previous_subsets_with_metadata(self) -> Sequence[AssetSubsetWithMetadata]:
        if self.node_cursor is None:
            return []
        return self.node_cursor.subsets_with_metadata

    @functools.cached_property
    @root_property
    def parent_will_update_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions whose parents will be updated on this tick, and which
        can be materialized in the same run as this asset.
        """
        subset = self.empty_subset()
        for parent_key in self.asset_graph.get(self.asset_key).parent_keys:
            if not self.materializable_in_same_run(self.asset_key, parent_key):
                continue
            parent_subset = self.request_subsets_by_key.get(parent_key)
            if not parent_subset:
                continue
            parent_subset = ValidAssetSubset.coerce_from_subset(
                parent_subset.convert_to_serializable_subset(), self.partitions_def
            )
            subset |= replace(parent_subset, key=self.asset_key)
        return subset

    @functools.cached_property
    @root_property
    def materialized_since_previous_tick_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return ValidAssetSubset.from_asset_partitions_set(
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
    def _previous_tick_discarded_subset(self) -> Optional[SerializableEntitySubset[AssetKey]]:
        """Fetches the unique id corresponding to the DiscardOnMaxMaterializationsExceededRule, if
        that rule is part of the broader condition.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            DiscardOnMaxMaterializationsExceededRule,
        )
        from dagster._core.definitions.declarative_automation.legacy.rule_condition import (
            RuleCondition,
        )
        from dagster._core.definitions.declarative_automation.operators import (
            NotAutomationCondition,
        )

        # if you have a discard condition, it'll be part of a structure of the form
        # Or(MaterializeCond, Not(SkipCond), Not(DiscardCond))
        if len(self.condition.children) != 3:
            return None
        unique_id = self.condition.get_node_unique_id(parent_unique_id=None, index=None)

        # get Not(DiscardCond)
        not_discard_condition = self.condition.children[2]
        unique_id = not_discard_condition.get_node_unique_id(parent_unique_id=unique_id, index=2)
        if not isinstance(not_discard_condition, NotAutomationCondition):
            return None

        # get DiscardCond
        discard_condition = not_discard_condition.children[0]
        unique_id = discard_condition.get_node_unique_id(parent_unique_id=unique_id, index=0)
        if not isinstance(discard_condition, RuleCondition) or not isinstance(
            discard_condition.rule, DiscardOnMaxMaterializationsExceededRule
        ):
            return None

        # grab the stored cursor value for the discard condition
        discard_cursor = (
            self.cursor.node_cursors_by_unique_id.get(unique_id) if self.cursor else None
        )
        return discard_cursor.true_subset if discard_cursor else None

    @property
    @root_property
    def previous_tick_requested_subset(self) -> SerializableEntitySubset:
        """The set of asset partitions that were requested (or discarded) on the previous tick."""
        if self.cursor is None:
            return self.empty_subset()

        discarded_subset = self._previous_tick_discarded_subset
        requested_subset = self.cursor.previous_requested_subset
        return (
            ValidAssetSubset.coerce_from_subset(requested_subset, self.partitions_def)
            | discarded_subset
            if discarded_subset
            else requested_subset
        )

    @property
    def materialized_requested_or_discarded_since_previous_tick_subset(self) -> ValidAssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return self.materialized_since_previous_tick_subset | self.previous_tick_requested_subset

    @functools.cached_property
    @root_property
    def _parent_has_updated_subset_and_new_latest_storage_id(
        self,
    ) -> tuple[ValidAssetSubset, Optional[int]]:
        """Returns the set of asset partitions whose parents have updated since the last time this
        condition was evaluated.
        """
        max_child_partitions_str = os.getenv("DAGSTER_MAX_AMP_CHILD_PARTITIONS", None)
        (
            asset_partitions,
            cursor,
        ) = self.root_context.instance_queryer.asset_partitions_with_newly_updated_parents_and_new_cursor(
            latest_storage_id=self.previous_max_storage_id,
            child_asset_key=self.root_context.asset_key,
            map_old_time_partitions=False,
            max_child_partitions=int(max_child_partitions_str)
            if max_child_partitions_str
            else None,
        )
        return ValidAssetSubset.from_asset_partitions_set(
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
        from dagster._core.definitions.declarative_automation.serialized_objects import (
            HistoricalAllPartitionsSubsetSentinel,
        )

        if not self.node_cursor:
            return self.candidate_subset
        # when the candidate_subset is HistoricalAllPartitionsSubsetSentinel, this indicates that the
        # entire asset was evaluated for this condition on the previous tick, and so no candidates
        # were *not* evaluated on the previous tick
        elif isinstance(self.node_cursor.candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return self.empty_subset()
        return self.candidate_subset - self.node_cursor.candidate_subset

    def materializable_in_same_run(self, child_key: AssetKey, parent_key: AssetKey) -> bool:
        """Returns whether a child asset can be materialized in the same run as a parent asset."""
        from dagster._core.definitions.assets.graph.asset_graph import executable_in_same_run

        return executable_in_same_run(self.asset_graph, child_key, parent_key)

    def get_parents_that_will_not_be_materialized_on_current_tick(
        self, *, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of parent asset partitions that will not be updated in the same run of
        this asset partition if a run is launched for this asset partition on this tick.
        """
        return {
            parent
            for parent in self.asset_graph.get_parents_partitions(
                asset_key=asset_partition.asset_key, partition_key=asset_partition.partition_key
            ).parent_partitions
            if not self.will_update_asset_partition(parent)
            or not self.materializable_in_same_run(asset_partition.asset_key, parent.asset_key)
        }

    def will_update_asset_partition(self, asset_partition: AssetKeyPartitionKey) -> bool:
        parent_subset = self.request_subsets_by_key.get(asset_partition.asset_key)
        if not parent_subset:
            return False
        return asset_partition in parent_subset.convert_to_serializable_subset()

    def add_evaluation_data_from_previous_tick(
        self,
        asset_partitions_by_frozen_metadata: Mapping[
            frozenset[tuple[str, MetadataValue]], AbstractSet[AssetKeyPartitionKey]
        ],
        ignore_subset: SerializableEntitySubset,
    ) -> tuple[ValidAssetSubset, Sequence[AssetSubsetWithMetadata]]:
        """Combines information calculated on this tick with information from the previous tick,
        returning a tuple of the combined true subset and the combined subsets with metadata.

        Args:
            asset_partitions_by_frozen_metadata: A mapping from metadata to the set of asset
                partitions that the rule applies to.
            ignore_subset: An EntitySubset which represents information that we should *not* carry
                forward from the previous tick.
        """
        from dagster._core.definitions.declarative_automation.serialized_objects import (
            AssetSubsetWithMetadata,
        )

        mapping = defaultdict(lambda: self.empty_subset())
        has_new_metadata_subset = self.empty_subset()
        for frozen_metadata, asset_partitions in asset_partitions_by_frozen_metadata.items():
            mapping[frozen_metadata] = ValidAssetSubset.from_asset_partitions_set(
                self.asset_key, self.partitions_def, asset_partitions
            )
            has_new_metadata_subset |= mapping[frozen_metadata]

        # don't use information from the previous tick if we have explicit metadata for it or
        # we've explicitly said to ignore it
        ignore_subset = has_new_metadata_subset | ignore_subset

        for elt in self.previous_subsets_with_metadata:
            carry_forward_subset = (
                ValidAssetSubset.coerce_from_subset(elt.subset, self.partitions_def) - ignore_subset
            )
            if carry_forward_subset.size > 0:
                mapping[elt.frozen_metadata] |= carry_forward_subset

        # for now, an asset is in the "true" subset if and only if we have some metadata for it
        true_subset = self.empty_subset()
        for subset in mapping.values():
            true_subset |= subset

        return (
            self.candidate_subset & true_subset,
            [
                AssetSubsetWithMetadata(subset=subset, metadata=dict(metadata))
                for metadata, subset in mapping.items()
            ],
        )

    def empty_subset(self) -> ValidAssetSubset:
        return ValidAssetSubset.empty(self.asset_key, self.partitions_def)
