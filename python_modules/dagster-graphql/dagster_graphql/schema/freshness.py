import graphene
from dagster._core.definitions.freshness import FreshnessState

GrapheneFreshnessState = graphene.Enum.from_enum(FreshnessState)


class GrapheneFreshnessStateRecord(graphene.ObjectType):
    class Meta:
        name = "FreshnessStateRecord"

    state = graphene.NonNull(GrapheneFreshnessState)
    updatedAt = graphene.NonNull(graphene.Float)
