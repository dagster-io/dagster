from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    NamedTuple,
    Optional,
)

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._serdes.serdes import (
    NamedTupleSerializer,
    UnpackContext,
    UnpackedValue,
    whitelist_for_serdes,
)

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule


class AutoMaterializePolicySerializer(NamedTupleSerializer):
    def before_unpack(
        self, context: UnpackContext, unpacked_dict: Dict[str, UnpackedValue]
    ) -> Dict[str, UnpackedValue]:
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        backcompat_map = {
            "on_missing": AutoMaterializeRule.materialize_on_missing(),
            "on_new_parent_data": AutoMaterializeRule.materialize_on_parent_updated(),
            "for_freshness": AutoMaterializeRule.materialize_on_required_for_freshness(),
        }

        # determine if this namedtuple was serialized with the old format (booleans for rules)
        if any(backcompat_key in unpacked_dict for backcompat_key in backcompat_map):
            # all old policies had this rule by default
            rules = {AutoMaterializeRule.skip_on_parent_outdated()}
            for backcompat_key, rule in backcompat_map.items():
                if unpacked_dict.get(backcompat_key):
                    rules.add(rule)
            unpacked_dict["rules"] = frozenset(rules)

        return unpacked_dict


class AutoMaterializePolicyType(Enum):
    EAGER = "EAGER"
    LAZY = "LAZY"


@experimental
@whitelist_for_serdes(
    old_fields={"time_window_partition_scope_minutes": 1e-6},
    serializer=AutoMaterializePolicySerializer,
)
class AutoMaterializePolicy(
    NamedTuple(
        "_AutoMaterializePolicy",
        [
            ("rules", FrozenSet["AutoMaterializeRule"]),
            ("max_materializations_per_minute", Optional[int]),
        ],
    )
):
    """An AutoMaterializePolicy specifies how Dagster should attempt to keep an asset up-to-date.

    There are two main kinds of auto-materialize policies: eager and lazy. In essence, an asset with
    an eager policy will try to immediately materialize after upstream changes, while an asset with
    a lazy policy will only materialize when necessary in order to satisfy the relevant
    FreshnessPolicies.

    For an asset / partition of an asset with an _eager_ policy to be auto-materialized, at least
    one of the following must be true:

    - it is missing
    - it has a freshness policy that requires more up-to-date data
    - any of its descendants have a freshness policy that require more up-to-date data
    - any of its parent assets / partitions have newer data

    For an asset / partition of an asset with a _lazy_ policy to be auto-materialized, at least one
    of the following must be true:

    - it has a freshness policy that requires more up-to-date data
    - any of its descendants have a freshness policy that require more up-to-date data

    If an asset / partition meets the above criteria, then it will be auto-materialized only if none
    of the following are true:

    - any of its parent assets / partitions are missing
    - any of its ancestor assets / partitions have ancestors of their own with newer data

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
    ):
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        check.invariant(
            max_materializations_per_minute is None or max_materializations_per_minute > 0,
            "max_materializations_per_minute must be positive. To disable rate-limiting, set it"
            " to None. To disable auto materializing, remove the policy.",
        )

        return super(AutoMaterializePolicy, cls).__new__(
            cls,
            rules=frozenset(check.set_param(rules, "rules", of_type=AutoMaterializeRule)),
            max_materializations_per_minute=max_materializations_per_minute,
        )

    @property
    def materialize_rules(self) -> AbstractSet["AutoMaterializeRule"]:
        from dagster._core.definitions.auto_materialize_condition import AutoMaterializeDecisionType

        return {
            rule
            for rule in self.rules
            if rule.decision_type == AutoMaterializeDecisionType.MATERIALIZE
        }

    @property
    def skip_rules(self) -> AbstractSet["AutoMaterializeRule"]:
        from dagster._core.definitions.auto_materialize_condition import AutoMaterializeDecisionType

        return {
            rule for rule in self.rules if rule.decision_type == AutoMaterializeDecisionType.SKIP
        }

    @public
    @staticmethod
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
            },
            max_materializations_per_minute=check.opt_int_param(
                max_materializations_per_minute, "max_materializations_per_minute"
            ),
        )

    @public
    @staticmethod
    def lazy(max_materializations_per_minute: Optional[int] = 1) -> "AutoMaterializePolicy":
        """Constructs a lazy AutoMaterializePolicy.

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
        """Constructs a copy of this policy with the specified rules added."""
        return self._replace(rules=self.rules.union(set(rules_to_add)))

    @property
    def policy_type(self) -> AutoMaterializePolicyType:
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        if AutoMaterializeRule.materialize_on_parent_updated() in self.rules:
            return AutoMaterializePolicyType.EAGER
        return AutoMaterializePolicyType.LAZY
