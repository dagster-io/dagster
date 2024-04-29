import dataclasses
import datetime
import functools
import logging
from dataclasses import dataclass
from typing import AbstractSet, Mapping, Optional, Tuple

import pendulum

from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
)
from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
    AssetConditionEvaluation,
    AssetConditionEvaluationState,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey

from .asset_condition_evaluation_context import AssetConditionEvaluationContext


@dataclass(frozen=True)
class SchedulingConditionEvaluationContext:
    # the AssetKey of the currently-evaluated asset
    asset_key: AssetKey

    # the condition that is being evaluated
    condition: AssetCondition
    # the unique identifier for this condition within the broader condition tree
    condition_unique_id: str

    # the subset of AssetPartitions for this Asset which must be evaluated. at the root of the
    # condition evaluation tree, this is the AllPartitionsSubset, but this may shrink as conditions
    # are applied and we can be certain that certain partitions will not be true for the overall
    # expression
    candidate_subset: ValidAssetSubset

    # a view of the AssetGraph that will be used to help compute properties of the asset during
    # computation
    asset_graph_view: AssetGraphView

    # the serialized information calculated during the previous evaluation of this condition
    # note that this refers to the evaluation of this specific node in the condition tree, not the
    # evaluation of the root of the tree
    # used to avoid recomputing information that we know has not changed since the previous tick
    previous_evaluation: Optional[AssetConditionEvaluation]

    # contains information about the previous evaluation of all assets within this asset's automation
    # policy sensor. this provides a pointer to the top-level condition in the evaluation tree, as
    # well as a few extra fields, such as the previous evaluation timestamp, and the max event id
    # at the time of that computation. this information is again used to avoid recomputing information
    # as well as detecting if anything has changed since the previous time this condition was evaluated
    previous_evaluation_state_by_key: Mapping[AssetKey, AssetConditionEvaluationState]
    # this is the same as the above, but for information that has been calculated during this tick.
    # it will be used to determine if a parent will be materialized on this tick
    current_evaluation_state_by_key: Mapping[AssetKey, AssetConditionEvaluationState]

    # the time at which this context object was created, allowing us to time the duration of an
    # evaluation for display in the UI
    create_time: datetime.datetime
    logger: logging.Logger

    # we need to continue supporting the current implementations of AutoMaterializeRules,
    # which rely on the legact context object. however, this object contains many fields
    # which are not relevant to the scheduling condition evaluation, and so keeping it
    # as a reference here makes it easy to remove it in the future.
    _legacy_context: AssetConditionEvaluationContext

    @functools.cached_property
    def candidate_slice(self) -> AssetSlice:
        return self.asset_graph_view.get_asset_slice_from_subset(self.candidate_subset)

    @property
    def legacy_context(self) -> AssetConditionEvaluationContext:
        return self._legacy_context

    @property
    def start_timestamp(self) -> float:
        return self.create_time.timestamp()

    @property
    def previous_evaluation_state(self) -> Optional[AssetConditionEvaluationState]:
        return self.previous_evaluation_state_by_key.get(self.asset_key)

    @property
    def new_max_storage_id(self) -> Optional[int]:
        # TODO: this should be pulled from the asset graph view
        return self._get_updated_parents_and_storage_id()[1]

    def _get_updated_parents_and_storage_id(
        self,
    ) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
        return self.asset_graph_view._queryer.asset_partitions_with_newly_updated_parents_and_new_cursor(  # noqa
            latest_storage_id=self.previous_evaluation_state.max_storage_id
            if self.previous_evaluation_state
            else None,
            child_asset_key=self.asset_key,
            map_old_time_partitions=False,
        )

    def for_child_condition(
        self, child_condition: AssetCondition, candidate_subset: ValidAssetSubset
    ):
        child_unique_id = child_condition.get_unique_id(parent_unique_id=self.condition_unique_id)
        return dataclasses.replace(
            self,
            condition=child_condition,
            condition_unique_id=child_unique_id,
            candidate_subset=candidate_subset,
            previous_evaluation=self.previous_evaluation.for_child(child_unique_id)
            if self.previous_evaluation
            else None,
            create_time=pendulum.now("UTC"),
            _legacy_context=self._legacy_context.for_child(
                child_condition, child_unique_id, candidate_subset
            ),
        )
