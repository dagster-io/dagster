import dagster._check as check
import graphene
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy,
    AutoMaterializePolicyType,
)
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeDecisionType,
    AutoMaterializeRule,
)

from .util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneAutoMaterializeRule(graphene.ObjectType):
    decisionType = graphene.NonNull(GrapheneAutoMaterializeDecisionType)
    description = graphene.String()

    def __init__(self, auto_materialize_rule: AutoMaterializeRule):
        super().__init__(
            decisionType=auto_materialize_rule.decision_type,
            description=auto_materialize_rule.description,
        )


class GrapheneAutoMaterializePolicy(graphene.ObjectType):
    policyType = graphene.NonNull(graphene.Enum.from_enum(AutoMaterializePolicyType))
    maxMaterializationsPerMinute = graphene.Int()
    rules = non_null_list(GrapheneAutoMaterializeRule)

    class Meta:
        name = "AutoMaterializePolicy"

    def __init__(self, auto_materialize_policy: AutoMaterializePolicy):
        auto_materialize_policy = check.inst_param(
            auto_materialize_policy, "auto_materialize_policy", AutoMaterializePolicy
        )
        super().__init__(
            rules=[GrapheneAutoMaterializeRule(rule) for rule in auto_materialize_policy.rules],
            policyType=auto_materialize_policy.policy_type,
            maxMaterializationsPerMinute=auto_materialize_policy.max_materializations_per_minute,
        )
