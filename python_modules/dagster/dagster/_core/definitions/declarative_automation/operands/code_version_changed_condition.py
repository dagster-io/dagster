from typing import Optional

from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


@whitelist_for_serdes
@record
class CodeVersionChangedCondition(AutomationCondition):
    label: Optional[str] = None

    @property
    def description(self) -> str:
        return "Asset code version changed since previous tick"

    @property
    def name(self) -> str:
        return "code_version_changed"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        previous_code_version = context.cursor
        current_code_version = context.asset_graph.get(context.asset_key).code_version
        if previous_code_version is None or previous_code_version == current_code_version:
            true_slice = context.get_empty_slice()
        else:
            true_slice = context.candidate_slice

        return AutomationResult(context, true_slice, cursor=current_code_version)
