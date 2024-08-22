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

    @property
    def requires_cursor(self) -> bool:
        return True

    def _get_previous_code_version(self, context: AutomationContext) -> Optional[str]:
        if context.node_cursor is None:
            return None
        return context.node_cursor.get_extra_state(as_type=str)

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        previous_code_version = self._get_previous_code_version(context)
        current_code_version = context.asset_graph.get(context.asset_key).code_version
        if previous_code_version is None or previous_code_version == current_code_version:
            true_slice = context.get_empty_slice()
        else:
            true_slice = context.candidate_slice

        return AutomationResult(context, true_slice, extra_state=current_code_version)
