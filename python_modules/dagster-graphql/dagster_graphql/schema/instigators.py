import graphene

from dagster_graphql.schema.schedules import GrapheneSchedule
from dagster_graphql.schema.sensors import GrapheneSensor


class GrapheneInstigator(graphene.Union):
    class Meta:
        types = (GrapheneSchedule, GrapheneSensor)
        name = "Instigator"
