import graphene
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
)

from dagster_graphql.schema.asset_condition_evaluations import get_expanded_label
from dagster_graphql.schema.util import non_null_list


class GrapheneAutomationCondition(graphene.ObjectType):
    label = graphene.Field(graphene.String)
    expandedLabel = non_null_list(graphene.String)

    class Meta:
        name = "AutomationCondition"

    def __init__(self, snapshot: AutomationConditionSnapshot):
        super().__init__(
            label=snapshot.node_snapshot.label,
            expandedLabel=get_expanded_label(snapshot),
        )
