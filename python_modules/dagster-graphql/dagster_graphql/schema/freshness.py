import graphene
from dagster._core.definitions.freshness import InternalFreshnessPolicy, TimeWindowFreshnessPolicy


class GrapheneTimeWindowFreshnessPolicy(graphene.ObjectType):
    class Meta:
        name = "TimeWindowFreshnessPolicy"

    failWindowSeconds = graphene.NonNull(graphene.Int)
    warnWindowSeconds = graphene.Int()


class GrapheneInternalFreshnessPolicy(graphene.Union):
    class Meta:
        name = "InternalFreshnessPolicy"
        types = (GrapheneTimeWindowFreshnessPolicy,)

    @classmethod
    def from_policy(cls, policy: InternalFreshnessPolicy):
        if isinstance(policy, TimeWindowFreshnessPolicy):
            return GrapheneTimeWindowFreshnessPolicy(
                failWindowSeconds=policy.fail_window.to_timedelta().total_seconds(),
                warnWindowSeconds=policy.warn_window.to_timedelta().total_seconds()
                if policy.warn_window
                else None,
            )
        raise Exception("Unknown freshness policy type")
