import dagster._check as check
import graphene
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy,
    AutoMaterializePolicyType,
)
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeDecisionType

from .util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneAutoMaterializeRule(graphene.ObjectType):
    description = graphene.NonNull(graphene.String)
    decisionType = GrapheneAutoMaterializeDecisionType

    class Meta:
        name = "AutoMaterializeRule"


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
            rules=[
                GrapheneAutoMaterializeRule(rule.description, rule.decision_type)
                for rule in auto_materialize_policy.rules
            ],
            policyType=auto_materialize_policy.policy_type,
            maxMaterializationsPerMinute=auto_materialize_policy.max_materializations_per_minute,
        )
