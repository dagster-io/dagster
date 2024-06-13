from ..automation_condition import AutomationCondition


class AssetCondition(AutomationCondition):
    """Deprecated: Use AutomationCondition instead."""

    @property
    def requires_cursor(self) -> bool:
        return True

    @staticmethod
    def parent_newer() -> "AutomationCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "AutomationCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "AutomationCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AutomationCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been updated
        since the latest tick of the given cron schedule. For partitioned assets with a time
        component, this can only be true for the most recent partition.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return ~RuleCondition(rule=AutoMaterializeRule.materialize_on_cron(cron_schedule, timezone))

    @staticmethod
    def parents_updated_since_cron(
        cron_schedule: str, timezone: str = "UTC"
    ) -> "AutomationCondition":
        """Returns an AssetCondition that is true for an asset partition when all parent asset
        partitions have been updated more recently than the latest tick of the given cron schedule.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return ~RuleCondition(
            rule=AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron(
                cron_schedule, timezone
            )
        )
