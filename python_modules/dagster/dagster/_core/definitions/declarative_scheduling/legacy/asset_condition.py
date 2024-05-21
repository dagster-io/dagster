from ..scheduling_condition import SchedulingCondition


class AssetCondition(SchedulingCondition):
    """Deprecated: Use SchedulingCondition instead."""

    @staticmethod
    def parent_newer() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "SchedulingCondition":
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
    ) -> "SchedulingCondition":
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
