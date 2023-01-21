import dagster._check as check
import graphene
from dagster._core.definitions.freshness_policy import FreshnessPolicy


class GrapheneAssetFreshnessInfo(graphene.ObjectType):
    currentMinutesLate = graphene.Field(graphene.Float)
    latestMaterializationMinutesLate = graphene.Field(graphene.Float)

    class Meta:
        name = "AssetFreshnessInfo"


class GrapheneFreshnessPolicy(graphene.ObjectType):
    maximumLagMinutes = graphene.NonNull(graphene.Float)
    cronSchedule = graphene.Field(graphene.String)

    class Meta:
        name = "FreshnessPolicy"

    def __init__(self, freshness_policy: FreshnessPolicy):
        freshness_policy = check.inst_param(freshness_policy, "freshness_policy", FreshnessPolicy)

        super().__init__(
            maximumLagMinutes=freshness_policy.maximum_lag_minutes,
            cronSchedule=freshness_policy.cron_schedule,
        )
