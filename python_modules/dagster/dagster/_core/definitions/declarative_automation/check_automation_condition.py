from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dagster._core.definitions.asset_key import AssetCheckKey
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )


class CheckAutomationCondition:
    """Helper class to provide static constructors for AutomationConditions that target AssetChecks."""

    @staticmethod
    def _status_condition(status_value: Optional[str]) -> "AutomationCondition[AssetCheckKey]":
        """Helper method to defer imports."""
        from dagster._core.definitions.declarative_automation.operands.slice_conditions import (
            LatestCheckStatusCondition,
        )
        from dagster._core.storage.asset_check_execution_record import (
            AssetCheckExecutionResolvedStatus,
        )

        status = AssetCheckExecutionResolvedStatus(status_value) if status_value else None
        return LatestCheckStatusCondition(target_status=status)

    @staticmethod
    def not_executed() -> "AutomationCondition[AssetCheckKey]":
        return CheckAutomationCondition._status_condition(None)

    @staticmethod
    def in_progress() -> "AutomationCondition[AssetCheckKey]":
        return CheckAutomationCondition._status_condition("IN_PROGRESS")

    @staticmethod
    def succeeded() -> "AutomationCondition[AssetCheckKey]":
        return CheckAutomationCondition._status_condition("SUCCEEDED")

    @staticmethod
    def skipped() -> "AutomationCondition[AssetCheckKey]":
        return CheckAutomationCondition._status_condition("SKIPPED")

    @staticmethod
    def failed() -> "AutomationCondition[AssetCheckKey]":
        return CheckAutomationCondition._status_condition("FAILED")
