from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import pytz

import dagster._check as check
from dagster._annotations import public
from dagster._utils.schedules import is_valid_cron_string

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_rule_evaluation import (
        AutoMaterializeDecisionType,
        AutoMaterializeRuleSnapshot,
    )
    from dagster._core.definitions.auto_materialize_rule_impls import (
        AutoMaterializeAssetPartitionsFilter,
        MaterializeOnCronRule,
        MaterializeOnMissingRule,
        MaterializeOnParentUpdatedRule,
        MaterializeOnRequiredForFreshnessRule,
        SkipOnBackfillInProgressRule,
        SkipOnNotAllParentsUpdatedRule,
        SkipOnNotAllParentsUpdatedSinceCronRule,
        SkipOnParentMissingRule,
        SkipOnParentOutdatedRule,
        SkipOnRequiredButNonexistentParentsRule,
        SkipOnRunInProgressRule,
    )
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationResult,
    )
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )
    from dagster._core.definitions.declarative_automation.legacy import RuleCondition


class AutoMaterializeRule(ABC):
    """An AutoMaterializeRule defines a bit of logic which helps determine if a materialization
    should be kicked off for a given asset partition.

    Each rule can have one of two decision types, `MATERIALIZE` (indicating that an asset partition
    should be materialized) or `SKIP` (indicating that the asset partition should not be
    materialized).

    Materialize rules are evaluated first, and skip rules operate over the set of candidates that
    are produced by the materialize rules. Other than that, there is no ordering between rules.
    """

    @property
    @abstractmethod
    def decision_type(self) -> "AutoMaterializeDecisionType":
        """The decision type of the rule (either `MATERIALIZE` or `SKIP`)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """A human-readable description of this rule. As a basic guideline, this string should
        complete the sentence: 'Indicates an asset should be (materialize/skipped) when ____'.
        """
        ...

    def to_asset_condition(self) -> "RuleCondition":
        """Converts this AutoMaterializeRule into an AssetCondition."""
        from dagster._core.definitions.declarative_automation.legacy.rule_condition import (
            RuleCondition,
        )

        return RuleCondition(rule=self)

    @abstractmethod
    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        """The core evaluation function for the rule. This function takes in a context object and
        returns a mapping from evaluated rules to the set of asset partitions that the rule applies
        to.
        """
        ...

    @public
    @staticmethod
    def materialize_on_required_for_freshness() -> "MaterializeOnRequiredForFreshnessRule":
        """(Deprecated) Materialize an asset partition if it is required to satisfy a freshness policy of this
        asset or one of its downstream assets.

        Note: This rule has no effect on partitioned assets.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            MaterializeOnRequiredForFreshnessRule,
        )

        return MaterializeOnRequiredForFreshnessRule()

    @public
    @staticmethod
    def materialize_on_cron(
        cron_schedule: str, timezone: str = "UTC", all_partitions: bool = False
    ) -> "MaterializeOnCronRule":
        """Materialize an asset partition if it has not been materialized since the latest cron
        schedule tick. For assets with a time component to their partitions_def, this rule will
        request all partitions that have been missed since the previous tick.

        Args:
            cron_schedule (str): A cron schedule string (e.g. "`0 * * * *`") indicating the ticks for
                which this rule should fire.
            timezone (str): The timezone in which this cron schedule should be evaluated. Defaults
                to "UTC".
            all_partitions (bool): If True, this rule fires for all partitions of this asset on each
                cron tick. If False, this rule fires only for the last partition of this asset.
                Defaults to False.
        """
        check.param_invariant(
            is_valid_cron_string(cron_schedule), "cron_schedule", "must be a valid cron string"
        )
        check.param_invariant(
            timezone in pytz.all_timezones_set, "timezone", "must be a valid timezone"
        )
        from dagster._core.definitions.auto_materialize_rule_impls import MaterializeOnCronRule

        return MaterializeOnCronRule(
            cron_schedule=cron_schedule, timezone=timezone, all_partitions=all_partitions
        )

    @public
    @staticmethod
    def materialize_on_parent_updated(
        updated_parent_filter: Optional["AutoMaterializeAssetPartitionsFilter"] = None,
    ) -> "MaterializeOnParentUpdatedRule":
        """Materialize an asset partition if one of its parents has been updated more recently
        than it has.

        Note: For time-partitioned or dynamic-partitioned assets downstream of an unpartitioned
        asset, this rule will only fire for the most recent partition of the downstream.

        Args:
            updated_parent_filter (Optional[AutoMaterializeAssetPartitionsFilter]): Filter to apply
                to updated parents. If a parent was updated but does not pass the filter criteria,
                then it won't count as updated for the sake of this rule.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            MaterializeOnParentUpdatedRule,
        )

        return MaterializeOnParentUpdatedRule(updated_parent_filter=updated_parent_filter)

    @public
    @staticmethod
    def materialize_on_missing() -> "MaterializeOnMissingRule":
        """Materialize an asset partition if it has never been materialized before. This rule will
        not fire for non-root assets unless that asset's parents have been updated.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import MaterializeOnMissingRule

        return MaterializeOnMissingRule()

    @public
    @staticmethod
    def skip_on_parent_missing() -> "SkipOnParentMissingRule":
        """Skip materializing an asset partition if one of its parent asset partitions has never
        been materialized (for regular assets) or observed (for observable source assets).
        """
        from dagster._core.definitions.auto_materialize_rule_impls import SkipOnParentMissingRule

        return SkipOnParentMissingRule()

    @public
    @staticmethod
    def skip_on_parent_outdated() -> "SkipOnParentOutdatedRule":
        """Skip materializing an asset partition if any of its parents has not incorporated the
        latest data from its ancestors.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import SkipOnParentOutdatedRule

        return SkipOnParentOutdatedRule()

    @public
    @staticmethod
    def skip_on_not_all_parents_updated(
        require_update_for_all_parent_partitions: bool = False,
    ) -> "SkipOnNotAllParentsUpdatedRule":
        """Skip materializing an asset partition if any of its parents have not been updated since
        the asset's last materialization.

        Args:
            require_update_for_all_parent_partitions (Optional[bool]): Applies only to an unpartitioned
                asset or an asset partition that depends on more than one partition in any upstream asset.
                If true, requires all upstream partitions in each upstream asset to be materialized since
                the downstream asset's last materialization in order to update it. If false, requires at
                least one upstream partition in each upstream asset to be materialized since the downstream
                asset's last materialization in order to update it. Defaults to false.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            SkipOnNotAllParentsUpdatedRule,
        )

        return SkipOnNotAllParentsUpdatedRule(require_update_for_all_parent_partitions)

    @staticmethod
    def skip_on_not_all_parents_updated_since_cron(
        cron_schedule: str, timezone: str = "UTC"
    ) -> "SkipOnNotAllParentsUpdatedSinceCronRule":
        """Skip materializing an asset partition if any of its parents have not been updated since
        the latest tick of the given cron schedule.

        Args:
            cron_schedule (str): A cron schedule string (e.g. "`0 * * * *`").
            timezone (str): The timezone in which this cron schedule should be evaluated. Defaults
                to "UTC".
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            SkipOnNotAllParentsUpdatedSinceCronRule,
        )

        return SkipOnNotAllParentsUpdatedSinceCronRule(
            cron_schedule=cron_schedule, timezone=timezone
        )

    @public
    @staticmethod
    def skip_on_required_but_nonexistent_parents() -> "SkipOnRequiredButNonexistentParentsRule":
        """Skip an asset partition if it depends on parent partitions that do not exist.

        For example, imagine a downstream asset is time-partitioned, starting in 2022, but has a
        time-partitioned parent which starts in 2023. This rule will skip attempting to materialize
        downstream partitions from before 2023, since the parent partitions do not exist.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            SkipOnRequiredButNonexistentParentsRule,
        )

        return SkipOnRequiredButNonexistentParentsRule()

    @public
    @staticmethod
    def skip_on_backfill_in_progress(
        all_partitions: bool = False,
    ) -> "SkipOnBackfillInProgressRule":
        """Skip an asset's partitions if targeted by an in-progress backfill.

        Args:
            all_partitions (bool): If True, skips all partitions of the asset being backfilled,
                regardless of whether the specific partition is targeted by a backfill.
                If False, skips only partitions targeted by a backfill. Defaults to False.
        """
        from dagster._core.definitions.auto_materialize_rule_impls import (
            SkipOnBackfillInProgressRule,
        )

        return SkipOnBackfillInProgressRule(all_partitions)

    @staticmethod
    def skip_on_run_in_progress() -> "SkipOnRunInProgressRule":
        from dagster._core.definitions.auto_materialize_rule_impls import SkipOnRunInProgressRule

        return SkipOnRunInProgressRule()

    def to_snapshot(self) -> "AutoMaterializeRuleSnapshot":
        """Returns a serializable snapshot of this rule for historical evaluations."""
        from dagster._core.definitions.auto_materialize_rule_evaluation import (
            AutoMaterializeRuleSnapshot,
        )

        return AutoMaterializeRuleSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            decision_type=self.decision_type,
        )

    def __eq__(self, other) -> bool:
        # override the default NamedTuple __eq__ method to factor in types
        return type(self) == type(other) and super().__eq__(other)

    def __hash__(self) -> int:
        # override the default NamedTuple __hash__ method to factor in types
        return hash(hash(type(self).__name__) + super().__hash__())
