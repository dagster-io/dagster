from dataclasses import dataclass
from typing import Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
@dataclass(frozen=True)
class CodeVersionChangedCondition(AutomationCondition[AssetKey]):
    label: Optional[str] = None

    @property
    def description(self) -> str:
        return "Asset code version changed since previous tick"

    @property
    def name(self) -> str:
        return "code_version_changed"

    def evaluate(self, context: AutomationContext) -> AutomationResult[AssetKey]:
        previous_code_version = context.cursor
        current_code_version = context.asset_graph.get(context.key).code_version
        if previous_code_version is None or previous_code_version == current_code_version:
            true_slice = context.get_empty_slice()
        else:
            true_slice = context.candidate_slice

        return AutomationResult(context, true_slice, cursor=current_code_version)
