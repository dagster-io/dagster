import dataclasses
from dataclasses import dataclass
from typing import Optional, Tuple

import dagster._check as check
import pendulum
from dagster import AssetKey
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_condition.asset_condition import (
    AndAssetCondition,
    AssetCondition,
    AssetConditionEvaluationState,
    AssetConditionResult,
)
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
    NewAssetConditionEvaluationContext,
)
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._seven.compat.pendulum import pendulum_freeze_time
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from ..scenario_state import ScenarioState


class FalseAssetCondition(AssetCondition):
    """Always returns the empty subset."""

    def description(self) -> str:
        return ""

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        if isinstance(context, NewAssetConditionEvaluationContext):
            return AssetConditionResult(
                condition=context.condition,
                start_timestamp=context.start_timestamp,
                end_timestamp=pendulum.now("UTC"),
                true_subset=context.get_empty_subset(),
                candidate_subset=context.candidate_slice.convert_to_valid_asset_subset(),
                subsets_with_metadata=[],
                child_results=[],
                extra_state=None,
            )
        else:
            return AssetConditionResult.create(context, true_subset=context.empty_subset())


@dataclass(frozen=True)
class AssetConditionScenarioState(ScenarioState):
    asset_condition: Optional[AssetCondition] = None
    previous_evaluation_state: Optional[AssetConditionEvaluationState] = None

    def evaluate_new(
        self, asset: CoercibleToAssetKey
    ) -> Tuple["AssetConditionScenarioState", AssetConditionResult]:
        asset_key = AssetKey.from_coercible(asset)
        # ensure that the top level condition never returns any asset partitions, as otherwise the
        # next evaluation will assume that those asset partitions were requested by the machinery
        asset_condition = AndAssetCondition(
            children=[check.not_none(self.asset_condition), FalseAssetCondition()]
        )
        with pendulum_freeze_time(self.current_time):
            asset_graph_view = AssetGraphView.for_test(self.defs, self.instance)
            candidate_slice = asset_graph_view.get_asset_slice(asset_key)

            context = NewAssetConditionEvaluationContext.create(
                condition=asset_condition,
                candidate_slice=candidate_slice,
                previous_evaluation_state=self.previous_evaluation_state,
            )

            full_result = asset_condition.evaluate(context)  # type: ignore
            new_state = dataclasses.replace(
                self,
                previous_evaluation_state=AssetConditionEvaluationState.create(
                    context,  # type: ignore
                    full_result,
                ),
            )
        return new_state, full_result.child_results[0]

    def evaluate(
        self, asset: CoercibleToAssetKey
    ) -> Tuple["AssetConditionScenarioState", AssetConditionResult]:
        asset_key = AssetKey.from_coercible(asset)
        # ensure that the top level condition never returns any asset partitions, as otherwise the
        # next evaluation will assume that those asset partitions were requested by the machinery
        asset_condition = AndAssetCondition(
            children=[check.not_none(self.asset_condition), FalseAssetCondition()]
        )

        with pendulum_freeze_time(self.current_time):
            instance_queryer = CachingInstanceQueryer(
                instance=self.instance, asset_graph=self.asset_graph
            )
            context = AssetConditionEvaluationContext.create(
                asset_key=asset_key,
                condition=asset_condition,
                previous_evaluation_state=self.previous_evaluation_state,
                instance_queryer=instance_queryer,
                data_time_resolver=CachingDataTimeResolver(instance_queryer),
                evaluation_state_by_key={},
                expected_data_time_mapping={},
                daemon_context=AssetDaemonContext(
                    evaluation_id=1,
                    instance=self.instance,
                    asset_graph=self.asset_graph,
                    cursor=AssetDaemonCursor.empty(),
                    materialize_run_tags={},
                    observe_run_tags={},
                    auto_observe_asset_keys=None,
                    auto_materialize_asset_keys=None,
                    respect_materialization_data_versions=False,
                    logger=self.logger,
                    evaluation_time=self.current_time,
                ),
            )

            full_result = asset_condition.evaluate(context)
            new_state = dataclasses.replace(
                self,
                previous_evaluation_state=AssetConditionEvaluationState.create(
                    context, full_result
                ),
            )

        return new_state, full_result.child_results[0]

    def without_previous_evaluation_state(self) -> "AssetConditionScenarioState":
        """Removes the previous evaluation state from the state. This is useful for testing
        re-evaluating this data "from scratch" after much computation has occurred.
        """
        return dataclasses.replace(self, previous_evaluation_state=None)
