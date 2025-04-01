from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, AbstractSet, NamedTuple, Optional  # noqa: UP035

from dagster_shared.serdes.serdes import (
    NamedTupleSerializer,
    UnpackContext,
    UnpackedValue,
    whitelist_for_serdes,
)

import dagster._check as check
from dagster._annotations import deprecated, public

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_rule import (
        AutoMaterializeRule,
        AutoMaterializeRuleSnapshot,
    )
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )


class AutoMaterializePolicySerializer(NamedTupleSerializer):
    def before_unpack(
        self, context: UnpackContext, unpacked_dict: dict[str, UnpackedValue]
    ) -> dict[str, UnpackedValue]:
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        backcompat_map = {
            "on_missing": AutoMaterializeRule.materialize_on_missing(),
            "on_new_parent_data": AutoMaterializeRule.materialize_on_parent_updated(),
            "for_freshness": AutoMaterializeRule.materialize_on_required_for_freshness(),
        }

        # determine if this namedtuple was serialized with the old format (booleans for rules)
        if any(backcompat_key in unpacked_dict for backcompat_key in backcompat_map):
            # all old policies had these rules by default
            rules = {
                AutoMaterializeRule.skip_on_parent_outdated(),
                AutoMaterializeRule.skip_on_parent_missing(),
                AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
                AutoMaterializeRule.skip_on_backfill_in_progress(),
            }
            for backcompat_key, rule in backcompat_map.items():
                if unpacked_dict.get(backcompat_key):
                    rules.add(rule)
            unpacked_dict["rules"] = frozenset(rules)

        return unpacked_dict


class AutoMaterializePolicyType(Enum):
    EAGER = "EAGER"
    LAZY = "LAZY"


@whitelist_for_serdes(
    old_fields={"time_window_partition_scope_minutes": 1e-6},
    serializer=AutoMaterializePolicySerializer,
)
@deprecated(breaking_version="1.10.0")
class AutoMaterializePolicy(
    NamedTuple(
        "_AutoMaterializePolicy",
        [
            ("rules", frozenset["AutoMaterializeRule"]),
            ("max_materializations_per_minute", Optional[int]),
            ("asset_condition", Optional["AutomationCondition"]),
        ],
    )
):
    """An AutoMaterializePolicy specifies how Dagster should attempt to keep an asset up-to-date.

    Each policy consists of a set of AutoMaterializeRules, which are used to determine whether an
    asset or a partition of an asset should or should not be auto-materialized.

    The most common policy is `AutoMaterializePolicy.eager()`, which consists of the following rules:

    - `AutoMaterializeRule.materialize_on_missing()`
        Materialize an asset or a partition if it has never been materialized.
    - `AutoMaterializeRule.materialize_on_parent_updated()`
        Materialize an asset or a partition if one of its parents have been updated more recently
        than it has.
    - `AutoMaterializeRule.materialize_on_required_for_freshness()`
        Materialize an asset or a partition if it is required to satisfy a freshness policy.
    - `AutoMaterializeRule.skip_on_parent_outdated()`
        Skip materializing an asset or partition if any of its parents have ancestors that have
        been materialized more recently.
    - `AutoMaterializeRule.skip_on_parent_missing()`
        Skip materializing an asset or a partition if any parent has never been materialized or
        observed.

    Policies can be customized by adding or removing rules. For example, if you'd like to allow
    an asset to be materialized even if some of its parent partitions are missing:

    .. code-block:: python

        from dagster import AutoMaterializePolicy, AutoMaterializeRule

        my_policy = AutoMaterializePolicy.eager().without_rules(
            AutoMaterializeRule.skip_on_parent_missing(),
        )

    If you'd like an asset to wait for all of its parents to be updated before materializing:

    .. code-block:: python

        from dagster import AutoMaterializePolicy, AutoMaterializeRule

        my_policy = AutoMaterializePolicy.eager().with_rules(
            AutoMaterializeRule.skip_on_all_parents_not_updated(),
        )

    Lastly, the `max_materializations_per_minute` parameter, which is set to 1 by default,
    rate-limits the number of auto-materializations that can occur for a particular asset within
    a short time interval. This mainly matters for partitioned assets. Its purpose is to provide a
    safeguard against "surprise backfills", where user-error causes auto-materialize to be
    accidentally triggered for large numbers of partitions at once.

    **Warning:**

    Constructing an AutoMaterializePolicy directly is not recommended as the API is subject to change.
    AutoMaterializePolicy.eager() and AutoMaterializePolicy.lazy() are the recommended API.

    """

    def __new__(
        cls,
        rules: AbstractSet["AutoMaterializeRule"],
        max_materializations_per_minute: Optional[int] = 1,
        asset_condition: Optional["AutomationCondition"] = None,
    ):
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        check.invariant(
            max_materializations_per_minute is None or max_materializations_per_minute > 0,
            "max_materializations_per_minute must be positive. To disable rate-limiting, set it"
            " to None. To disable auto materializing, remove the policy.",
        )
        check.param_invariant(
            bool(rules) ^ bool(asset_condition),
            "asset_condition",
            "Must specify exactly one of `rules` or `asset_condition`.",
        )
        if asset_condition is not None:
            check.param_invariant(
                max_materializations_per_minute is None,
                "max_materializations_per_minute",
                "`max_materializations_per_minute` is not supported when using `asset_condition`.",
            )

        return super().__new__(
            cls,
            rules=frozenset(check.set_param(rules, "rules", of_type=AutoMaterializeRule)),
            max_materializations_per_minute=max_materializations_per_minute,
            asset_condition=asset_condition,
        )

    @property
    def materialize_rules(self) -> AbstractSet["AutoMaterializeRule"]:
        from dagster._core.definitions.auto_materialize_rule_evaluation import (
            AutoMaterializeDecisionType,
        )

        return {
            rule
            for rule in self.rules
            if rule.decision_type == AutoMaterializeDecisionType.MATERIALIZE
        }

    @property
    def skip_rules(self) -> AbstractSet["AutoMaterializeRule"]:
        from dagster._core.definitions.auto_materialize_rule_evaluation import (
            AutoMaterializeDecisionType,
        )

        return {
            rule for rule in self.rules if rule.decision_type == AutoMaterializeDecisionType.SKIP
        }

    @staticmethod
    def from_automation_condition(
        automation_condition: "AutomationCondition",
    ) -> "AutoMaterializePolicy":
        """Constructs an AutoMaterializePolicy which will materialize an asset partition whenever
        the provided automation_condition evaluates to True.

        Args:
            automation_condition (AutomationCondition): The condition which determines whether an asset
                partition should be materialized.
        """
        return AutoMaterializePolicy(
            rules=set(), max_materializations_per_minute=None, asset_condition=automation_condition
        )

    @public
    @staticmethod
    @deprecated(
        breaking_version="1.10.0",
        additional_warn_text="Use `AutomationCondition.eager()` instead.",
    )
    def eager(max_materializations_per_minute: Optional[int] = 1) -> "AutoMaterializePolicy":
        """Constructs an eager AutoMaterializePolicy.

        Args:
            max_materializations_per_minute (Optional[int]): The maximum number of
                auto-materializations for this asset that may be initiated per minute. If this limit
                is exceeded, the partitions which would have been materialized will be discarded,
                and will require manual materialization in order to be updated. Defaults to 1.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        return AutoMaterializePolicy(
            rules={
                AutoMaterializeRule.materialize_on_missing(),
                AutoMaterializeRule.materialize_on_parent_updated(),
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                AutoMaterializeRule.skip_on_parent_outdated(),
                AutoMaterializeRule.skip_on_parent_missing(),
                AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
                AutoMaterializeRule.skip_on_backfill_in_progress(),
            },
            max_materializations_per_minute=check.opt_int_param(
                max_materializations_per_minute, "max_materializations_per_minute"
            ),
        )

    @public
    @staticmethod
    @deprecated(
        breaking_version="1.10.0",
        additional_warn_text="Use `AutomationCondition.any_downstream_conditions()` instead.",
    )
    def lazy(max_materializations_per_minute: Optional[int] = 1) -> "AutoMaterializePolicy":
        """(Deprecated) Constructs a lazy AutoMaterializePolicy.

        Args:
            max_materializations_per_minute (Optional[int]): The maximum number of
                auto-materializations for this asset that may be initiated per minute. If this limit
                is exceeded, the partitions which would have been materialized will be discarded,
                and will require manual materialization in order to be updated. Defaults to 1.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        return AutoMaterializePolicy(
            rules={
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                AutoMaterializeRule.skip_on_parent_outdated(),
                AutoMaterializeRule.skip_on_parent_missing(),
                AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
                AutoMaterializeRule.skip_on_backfill_in_progress(),
            },
            max_materializations_per_minute=check.opt_int_param(
                max_materializations_per_minute, "max_materializations_per_minute"
            ),
        )

    @public
    def without_rules(self, *rules_to_remove: "AutoMaterializeRule") -> "AutoMaterializePolicy":
        """Constructs a copy of this policy with the specified rules removed. Raises an error
        if any of the arguments are not rules in this policy.
        """
        non_matching_rules = set(rules_to_remove).difference(self.rules)
        check.param_invariant(
            not non_matching_rules,
            "rules_to_remove",
            f"Rules {[rule for rule in rules_to_remove if rule in non_matching_rules]} do not"
            " exist in this policy.",
        )
        return self._replace(
            rules=self.rules.difference(set(rules_to_remove)),
        )

    @public
    def with_rules(self, *rules_to_add: "AutoMaterializeRule") -> "AutoMaterializePolicy":
        """Constructs a copy of this policy with the specified rules added. If an instance of a
        provided rule with the same type exists on this policy, it will be replaced.
        """
        new_rule_types = {type(rule) for rule in rules_to_add}
        return self._replace(
            rules=set(rules_to_add).union(
                {rule for rule in self.rules if type(rule) not in new_rule_types}
            )
        )

    @property
    def policy_type(self) -> AutoMaterializePolicyType:
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        if AutoMaterializeRule.materialize_on_parent_updated() in self.rules:
            return AutoMaterializePolicyType.EAGER
        return AutoMaterializePolicyType.LAZY

    @property
    def rule_snapshots(self) -> Sequence["AutoMaterializeRuleSnapshot"]:
        return [rule.to_snapshot() for rule in self.rules]

    def to_automation_condition(self) -> "AutomationCondition":
        """Converts a set of materialize / skip rules into a single binary expression."""
        from dagster._core.definitions.auto_materialize_rule_impls import (
            DiscardOnMaxMaterializationsExceededRule,
        )
        from dagster._core.definitions.declarative_automation.operators import (
            AndAutomationCondition,
            NotAutomationCondition,
            OrAutomationCondition,
        )

        if self.asset_condition is not None:
            return self.asset_condition

        materialize_condition = OrAutomationCondition(
            operands=[
                rule.to_asset_condition()
                for rule in sorted(self.materialize_rules, key=lambda rule: rule.description)
            ]
        )
        skip_condition = OrAutomationCondition(
            operands=[
                rule.to_asset_condition()
                for rule in sorted(self.skip_rules, key=lambda rule: rule.description)
            ]
        )
        children = [
            materialize_condition,
            NotAutomationCondition(operand=skip_condition),
        ]
        if self.max_materializations_per_minute:
            discard_condition = DiscardOnMaxMaterializationsExceededRule(
                self.max_materializations_per_minute
            ).to_asset_condition()
            children.append(NotAutomationCondition(operand=discard_condition))

        # results in an expression of the form (m1 | m2 | ... | mn) & ~(s1 | s2 | ... | sn) & ~d
        return AndAutomationCondition(operands=children)

    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other)
            or self.to_automation_condition() == other.to_automation_condition()
        )
