import dagster._check as check
import graphene
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._time import get_current_datetime


class GrapheneAssetFreshnessInfo(graphene.ObjectType):
    # How old is the current data
    currentLagMinutes = graphene.Field(graphene.Float)
    # How overdue is the current data (currentLagMinutes - maximumLagMinutes)
    currentMinutesLate = graphene.Field(graphene.Float)
    latestMaterializationMinutesLate = graphene.Field(graphene.Float)

    class Meta:
        name = "AssetFreshnessInfo"


class GrapheneFreshnessPolicy(graphene.ObjectType):
    maximumLagMinutes = graphene.NonNull(graphene.Float)
    cronSchedule = graphene.Field(graphene.String)
    cronScheduleTimezone = graphene.Field(graphene.String)
    lastEvaluationTimestamp = graphene.Field(graphene.String)

    class Meta:
        name = "FreshnessPolicy"

    def __init__(self, freshness_policy: LegacyFreshnessPolicy):
        self._freshness_policy = check.inst_param(
            freshness_policy, "freshness_policy", LegacyFreshnessPolicy
        )

        super().__init__(
            maximumLagMinutes=self._freshness_policy.maximum_lag_minutes,
            cronSchedule=self._freshness_policy.cron_schedule,
            cronScheduleTimezone=self._freshness_policy.cron_schedule_timezone,
        )

    def resolve_lastEvaluationTimestamp(self, _graphene_info):
        # Note: This is presented as a string in milliseconds (JS timestamp)
        # for consistency with the asset materialization timestamps
        tick = self._freshness_policy.get_evaluation_tick(get_current_datetime())
        return str(int(tick.timestamp() * 1000)) if tick else None
