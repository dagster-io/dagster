import dataclasses
import datetime
import functools
from dataclasses import dataclass
from typing import AbstractSet, Mapping, Optional, Tuple

import pendulum

from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.declarative_scheduling.asset_condition import (
    AssetCondition,
    AssetConditionEvaluation,
    AssetConditionEvaluationState,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

from .asset_condition_evaluation_context import AssetConditionEvaluationContext


@dataclass(frozen=True)
class SchedulingConditionEvaluationContext:
    asset_key: AssetKey

    condition: AssetCondition
    condition_unique_id: str
    candidate_subset: ValidAssetSubset

    asset_graph_view: AssetGraphView

    previous_evaluation: Optional[AssetConditionEvaluation]
    previous_evaluation_state_by_key: Mapping[AssetKey, AssetConditionEvaluationState]
    current_evaluation_state_by_key: Mapping[AssetKey, AssetConditionEvaluationState]

    create_time: datetime.datetime

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
        self,
        child_condition: AssetCondition,
        candidate_subset: ValidAssetSubset,
        asset_key: Optional[AssetKey] = None,
    ):
        child_unique_id = child_condition.get_unique_id(parent_unique_id=self.condition_unique_id)
        return dataclasses.replace(
            self,
            asset_key=asset_key or self.asset_key,
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
