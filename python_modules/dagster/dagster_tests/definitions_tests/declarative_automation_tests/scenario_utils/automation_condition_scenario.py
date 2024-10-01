import dataclasses
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

import dagster._check as check
import mock
from dagster import AssetKey
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionCursor,
)
from dagster._core.definitions.events import AssetKeyPartitionKey, CoercibleToAssetKey
from dagster._core.test_utils import freeze_time

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state import (
    ScenarioState,
)


class FalseAutomationCondition(AutomationCondition):
    """Always returns the empty subset."""

    label: Optional[str] = None

    @property
    def description(self) -> str:
        return ""

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        return AutomationResult(context, true_subset=context.get_empty_subset())


@dataclass(frozen=True)
class AutomationConditionScenarioState(ScenarioState):
    automation_condition: Optional[AutomationCondition] = None
    condition_cursor: Optional[AutomationConditionCursor] = None
    requested_asset_partitions: Optional[Sequence[AssetKeyPartitionKey]] = None
    ensure_empty_result: bool = True
    request_backfills: bool = False

    def _get_current_results_by_key(
        self, asset_graph_view: AssetGraphView
    ) -> Mapping[AssetKey, AutomationResult]:
        if self.requested_asset_partitions is None:
            return {}
        ap_by_key = defaultdict(set)
        for ap in self.requested_asset_partitions:
            ap_by_key[ap.asset_key].add(ap)
        return {
            asset_key: mock.MagicMock(
                true_subset=asset_graph_view.get_asset_subset_from_asset_partitions(asset_key, aps),
                cursor=None,
            )
            for asset_key, aps in ap_by_key.items()
        }

    def evaluate(
        self, asset: CoercibleToAssetKey
    ) -> Tuple["AutomationConditionScenarioState", AutomationResult]:
        asset_key = AssetKey.from_coercible(asset)
        # ensure that the top level condition never returns any asset partitions, as otherwise the
        # next evaluation will assume that those asset partitions were requested by the machinery
        asset_condition = (
            AndAutomationCondition(
                operands=[check.not_none(self.automation_condition), FalseAutomationCondition()]
            )
            if self.ensure_empty_result
            else check.not_none(self.automation_condition)
        )
        asset_graph = self.scenario_spec.with_asset_properties(
            keys=[asset],
            auto_materialize_policy=AutoMaterializePolicy.from_automation_condition(
                asset_condition
            ),
        ).asset_graph

        with freeze_time(self.current_time):
            evaluator = AutomationConditionEvaluator(
                asset_graph=asset_graph,
                instance=self.instance,
                entity_keys=asset_graph.all_asset_keys,
                cursor=AssetDaemonCursor.empty().with_updates(
                    0, 0, [], [self.condition_cursor] if self.condition_cursor else []
                ),
                logger=self.logger,
                allow_backfills=False,
            )
            evaluator.current_results_by_key = self._get_current_results_by_key(
                evaluator.asset_graph_view
            )  # type: ignore
            context = AutomationContext.create(key=asset_key, evaluator=evaluator)

            full_result = asset_condition.evaluate(context)
            new_state = dataclasses.replace(self, condition_cursor=full_result.get_new_cursor())
            result = full_result.child_results[0] if self.ensure_empty_result else full_result

        return new_state, result

    def without_cursor(self) -> "AutomationConditionScenarioState":
        """Removes the previous evaluation state from the state. This is useful for testing
        re-evaluating this data "from scratch" after much computation has occurred.
        """
        return dataclasses.replace(self, condition_cursor=None)

    def with_requested_asset_partitions(
        self, requested_asset_partitions: Sequence[AssetKeyPartitionKey]
    ) -> "AutomationConditionScenarioState":
        return dataclasses.replace(self, requested_asset_partitions=requested_asset_partitions)
