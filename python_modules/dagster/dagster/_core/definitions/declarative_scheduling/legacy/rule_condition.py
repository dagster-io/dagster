from typing import Optional

from dagster._annotations import experimental
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.security import non_secure_md5_hash_str

from ..scheduling_condition import SchedulingResult
from ..scheduling_context import SchedulingContext
from .asset_condition import AssetCondition


@experimental
@whitelist_for_serdes
class RuleCondition(AssetCondition):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    rule: AutoMaterializeRule

    def get_unique_id(self, parent_unique_id: Optional[str]) -> str:
        # preserves old (bad) behavior of not including the parent_unique_id to avoid inavlidating
        # old serialized information
        parts = [self.rule.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @property
    def description(self) -> str:
        return self.rule.description

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        context.legacy_context.root_context.daemon_context.logger.debug(
            f"Evaluating rule: {self.rule.to_snapshot()}"
        )
        evaluation_result = self.rule.evaluate_for_asset(context)
        context.legacy_context.root_context.daemon_context.logger.debug(
            f"Rule returned {evaluation_result.true_subset.size} partitions "
            f"({evaluation_result.end_timestamp - evaluation_result.start_timestamp:.2f} seconds)"
        )
        return evaluation_result
