import dataclasses
from dataclasses import dataclass
from typing import Optional, Tuple

import dagster._check as check
from dagster import AssetKey
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_scheduling.legacy.legacy_context import (
    LegacyRuleEvaluationContext,
)
from dagster._core.definitions.declarative_scheduling.operators.boolean_operators import (
    AndAssetCondition,
)
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
    SchedulingResult,
)
from dagster._core.definitions.declarative_scheduling.scheduling_context import (
    SchedulingContext,
)
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    SchedulingEvaluationInfo,
)
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionEvaluationState,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._seven.compat.pendulum import pendulum_freeze_time
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from ..scenario_state import ScenarioState


class FalseAssetCondition(SchedulingCondition):
    """Always returns the empty subset."""

    @property
    def description(self) -> str:
        return ""

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        return SchedulingResult.create(
            context,
            true_subset=context.asset_graph_view.create_empty_slice(
                context.asset_key
            ).convert_to_valid_asset_subset(),
        )


@dataclass(frozen=True)
class AssetConditionScenarioState(ScenarioState):
    asset_condition: Optional[SchedulingCondition] = None
    previous_evaluation_state: Optional[AssetConditionEvaluationState] = None

    def evaluate(
        self, asset: CoercibleToAssetKey
    ) -> Tuple["AssetConditionScenarioState", SchedulingResult]:
        asset_key = AssetKey.from_coercible(asset)
        # ensure that the top level condition never returns any asset partitions, as otherwise the
        # next evaluation will assume that those asset partitions were requested by the machinery
        asset_condition = AndAssetCondition(
            operands=[check.not_none(self.asset_condition), FalseAssetCondition()]
        )
        asset_graph = self.scenario_spec.with_asset_properties(
            asset,
            auto_materialize_policy=AutoMaterializePolicy.from_asset_condition(asset_condition),
        ).asset_graph

        with pendulum_freeze_time(self.current_time):
            instance_queryer = CachingInstanceQueryer(
                instance=self.instance, asset_graph=asset_graph
            )
            daemon_context = AssetDaemonContext(
                evaluation_id=1,
                instance=self.instance,
                asset_graph=asset_graph,
                cursor=AssetDaemonCursor.empty(),
                materialize_run_tags={},
                observe_run_tags={},
                auto_observe_asset_keys=None,
                auto_materialize_asset_keys=None,
                respect_materialization_data_versions=False,
                logger=self.logger,
                evaluation_time=self.current_time,
            )
            legacy_context = LegacyRuleEvaluationContext.create(
                asset_key=asset_key,
                condition=asset_condition,
                previous_evaluation_state=self.previous_evaluation_state,
                instance_queryer=instance_queryer,
                data_time_resolver=CachingDataTimeResolver(instance_queryer),
                evaluation_state_by_key={},
                expected_data_time_mapping={},
                daemon_context=daemon_context,
            )
            context = SchedulingContext.create(
                asset_key=asset_key,
                asset_graph_view=daemon_context.asset_graph_view,
                logger=self.logger,
                current_tick_evaluation_info_by_key={},
                previous_evaluation_info=SchedulingEvaluationInfo.from_asset_condition_evaluation_state(
                    daemon_context.asset_graph_view, self.previous_evaluation_state
                )
                if self.previous_evaluation_state
                else None,
                legacy_context=legacy_context,
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
