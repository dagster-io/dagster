import dataclasses
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

import dagster._check as check
import mock
from dagster import AssetKey
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.legacy.legacy_context import (
    LegacyRuleEvaluationContext,
)
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionCursor,
)
from dagster._core.definitions.events import AssetKeyPartitionKey, CoercibleToAssetKey
from dagster._core.test_utils import freeze_time
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .scenario_state import ScenarioState


class FalseAutomationCondition(AutomationCondition):
    """Always returns the empty subset."""

    label: Optional[str] = None

    @property
    def description(self) -> str:
        return ""

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        return AutomationResult(context, true_slice=context.get_empty_slice())


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
                true_slice=asset_graph_view.get_asset_slice_from_subset(
                    AssetSubset.from_asset_partitions_set(
                        asset_key, asset_graph_view.asset_graph.get(asset_key).partitions_def, aps
                    )
                ),
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
                request_backfills=self.request_backfills,
            )
            legacy_context = LegacyRuleEvaluationContext.create_within_asset_daemon(
                asset_key=asset_key,
                condition=asset_condition,
                previous_condition_cursor=self.condition_cursor,
                instance_queryer=instance_queryer,
                data_time_resolver=CachingDataTimeResolver(instance_queryer),
                current_results_by_key={},
                expected_data_time_mapping={},
                daemon_context=daemon_context,
            )
            context = AutomationContext.create(
                asset_key=asset_key,
                asset_graph_view=daemon_context.asset_graph_view,
                logger=self.logger,
                current_tick_results_by_key=self._get_current_results_by_key(
                    daemon_context.asset_graph_view
                ),
                condition_cursor=self.condition_cursor,
                legacy_context=legacy_context,
            )

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
