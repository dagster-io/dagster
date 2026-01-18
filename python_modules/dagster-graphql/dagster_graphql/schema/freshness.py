import graphene
from dagster._core.definitions.freshness import (
    CronFreshnessPolicy,
    FreshnessPolicy,
    TimeWindowFreshnessPolicy,
)

from dagster_graphql.schema.asset_health import (
    GrapheneAssetHealthFreshnessMeta,
    GrapheneAssetHealthStatus,
)


class GrapheneFreshnessStatusInfo(graphene.ObjectType):
    freshnessStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    freshnessStatusMetadata = graphene.Field(GrapheneAssetHealthFreshnessMeta)

    class Meta:
        name = "FreshnessStatusInfo"


class GrapheneTimeWindowFreshnessPolicy(graphene.ObjectType):
    class Meta:
        name = "TimeWindowFreshnessPolicy"

    failWindowSeconds = graphene.NonNull(graphene.Int)
    warnWindowSeconds = graphene.Int()


class GrapheneCronFreshnessPolicy(graphene.ObjectType):
    class Meta:
        name = "CronFreshnessPolicy"

    deadlineCron = graphene.NonNull(graphene.String)
    lowerBoundDeltaSeconds = graphene.NonNull(graphene.Int)
    timezone = graphene.NonNull(graphene.String)


class GrapheneInternalFreshnessPolicy(graphene.Union):
    class Meta:
        name = "InternalFreshnessPolicy"
        types = (GrapheneTimeWindowFreshnessPolicy, GrapheneCronFreshnessPolicy)

    @classmethod
    def from_policy(cls, policy: FreshnessPolicy):
        if isinstance(policy, TimeWindowFreshnessPolicy):
            return GrapheneTimeWindowFreshnessPolicy(
                failWindowSeconds=policy.fail_window.to_timedelta().total_seconds(),
                warnWindowSeconds=policy.warn_window.to_timedelta().total_seconds()
                if policy.warn_window
                else None,
            )
        elif isinstance(policy, CronFreshnessPolicy):
            return GrapheneCronFreshnessPolicy(
                deadlineCron=policy.deadline_cron,
                lowerBoundDeltaSeconds=policy.lower_bound_delta.total_seconds(),
                timezone=policy.timezone,
            )
        raise Exception("Unknown freshness policy type")
