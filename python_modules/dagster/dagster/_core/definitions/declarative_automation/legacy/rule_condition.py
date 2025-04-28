from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._record import record
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )


@whitelist_for_serdes
@record
class RuleCondition(BuiltinAutomationCondition[AssetKey]):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    rule: AutoMaterializeRule

    def get_node_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        # preserves old (bad) behavior of not including the parent_unique_id to avoid invalidating
        # old serialized information
        parts = [self.rule.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @property
    def description(self) -> str:
        return self.rule.description

    def evaluate(self, context: "AutomationContext[AssetKey]") -> AutomationResult[AssetKey]:
        context.log.debug(f"Evaluating rule: {self.rule.to_snapshot()}")
        # Allow for access to legacy context in legacy rule evaluation
        evaluation_result = self.rule.evaluate_for_asset(context)
        context.log.debug(
            f"Rule returned {evaluation_result.true_subset.size} partitions "
            f"({evaluation_result.end_timestamp - evaluation_result.start_timestamp:.2f} seconds)"
        )
        return evaluation_result
