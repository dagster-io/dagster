import dagster._check as check
import graphene
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy,
    AutoMaterializePolicyType,
)


class GrapheneAutoMaterializePolicy(graphene.ObjectType):
    policyType = graphene.NonNull(graphene.Enum.from_enum(AutoMaterializePolicyType))
    maxMaterializationsPerMinute = graphene.Int()

    class Meta:
        name = "AutoMaterializePolicy"

    def __init__(self, auto_materialize_policy: AutoMaterializePolicy):
        auto_materialize_policy = check.inst_param(
            auto_materialize_policy, "auto_materialize_policy", AutoMaterializePolicy
        )
        super().__init__(
            policyType=auto_materialize_policy.policy_type,
            maxMaterializationsPerMinute=auto_materialize_policy.max_materializations_per_minute,
        )
