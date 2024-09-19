import dagster._check as check
import graphene
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy,
    AutoMaterializePolicyType,
)
from dagster._core.definitions.auto_materialize_rule_impls import (
    AutoMaterializeDecisionType,
    DiscardOnMaxMaterializationsExceededRule,
)

from dagster_graphql.schema.util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneAutoMaterializeRule(graphene.ObjectType):
    description = graphene.NonNull(graphene.String)
    decisionType = graphene.NonNull(GrapheneAutoMaterializeDecisionType)
    className = graphene.NonNull(graphene.String)

    class Meta:
        name = "AutoMaterializeRule"

    def __init__(self, description: str, decision_type: AutoMaterializeDecisionType):
        super().__init__(
            decisionType=decision_type,
            description=description,
            # the class name just needs to be distinct for each rule, so we use the description
            className=description,
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
        # for now, we don't represent the max materializations per minute rule as a proper
        # rule in the serialized AutoMaterializePolicy object, but do so in the GraphQL layer
        rules = [
            GrapheneAutoMaterializeRule(rule.description, rule.decision_type)
            for rule in auto_materialize_policy.rules
        ]
        if auto_materialize_policy.max_materializations_per_minute:
            rules.append(
                GrapheneAutoMaterializeRule(
                    description=DiscardOnMaxMaterializationsExceededRule(
                        limit=auto_materialize_policy.max_materializations_per_minute
                    ).description,
                    decision_type=AutoMaterializeDecisionType.DISCARD,
                )
            )
        super().__init__(
            rules=rules,
            policyType=auto_materialize_policy.policy_type,
            maxMaterializationsPerMinute=auto_materialize_policy.max_materializations_per_minute,
        )
