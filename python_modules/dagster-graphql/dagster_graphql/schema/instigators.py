import graphene

from .sensors import GrapheneSensor
from .schedules import GrapheneSchedule


class GrapheneInstigator(graphene.Union):
    class Meta:
        types = (GrapheneSchedule, GrapheneSensor)
        name = "Instigator"
