import graphene

from .schedules import GrapheneSchedule
from .sensors import GrapheneSensor


class GrapheneInstigator(graphene.Union):
    class Meta:
        types = (GrapheneSchedule, GrapheneSensor)
        name = "Instigator"
