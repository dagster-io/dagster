import dataclasses
from dataclasses import dataclass
from typing import Optional, Tuple

import dagster._check as check
from dagster import AssetKey
from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
    AssetConditionEvaluationState,
    AssetConditionResult,
)
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.instance import DagsterInstance
from dagster._seven.compat.pendulum import pendulum_freeze_time
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .asset_scenario_state import AssetScenarioState


@dataclass(frozen=True)
class AssetConditionScenarioState(AssetScenarioState):
    asset_condition: Optional[AssetCondition] = None
    previous_evaluation_state: Optional[AssetConditionEvaluationState] = None

    @staticmethod
    def create_from_state(
        state: AssetScenarioState, asset_condition: AssetCondition
    ) -> "AssetConditionScenarioState":
        return AssetConditionScenarioState(
            **{
                **{f.name: getattr(state, f.name) for f in dataclasses.fields(state)},
                "scenario_instance": DagsterInstance.ephemeral(),
                "asset_condition": asset_condition,
            },
        )

    def evaluate(
        self, asset: CoercibleToAssetKey
    ) -> Tuple["AssetConditionScenarioState", AssetConditionResult]:
        asset_key = AssetKey.from_coercible(asset)
        asset_condition = check.not_none(self.asset_condition)

        with pendulum_freeze_time(self.current_time):
            context = AssetConditionEvaluationContext.create(
                asset_key=asset_key,
                condition=asset_condition,
                previous_evaluation_state=self.previous_evaluation_state,
                instance_queryer=CachingInstanceQueryer(
                    instance=self.instance,
                    asset_graph=self.asset_graph,
                ),
                data_time_resolver=None,  # type: ignore
                evaluation_state_by_key={},
                expected_data_time_mapping={},
                # If you are an intrepid developer who has added a new field to AssetDaemonContext and
                # have found yourself here, it's likely that you can just set the value to None and
                # 'type: ignore' it. Most fields will not be accessed in these tests.
                daemon_context=AssetDaemonContext(
                    evaluation_id=1,
                    instance=self.instance,
                    asset_graph=self.asset_graph,
                    cursor=None,  # type: ignore
                    materialize_run_tags={},
                    observe_run_tags={},
                    auto_observe_asset_keys=None,
                    auto_materialize_asset_keys=None,
                    respect_materialization_data_versions=False,
                    logger=self.logger,
                    evaluation_time=self.current_time,
                ),
                is_scheduling_policy_evaluation=False,
            )

            result = asset_condition.evaluate(context)
            new_state = dataclasses.replace(
                self,
                previous_evaluation_state=AssetConditionEvaluationState.create(context, result),
            )

        return new_state, result

    def without_previous_evaluation_state(self) -> "AssetConditionScenarioState":
        """Removes the previous evaluation state from the state. This is useful for testing
        re-evaluating this data "from scratch" after much computation has occurred.
        """
        return dataclasses.replace(self, previous_evaluation_state=None)
