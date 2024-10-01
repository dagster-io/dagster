import graphene
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)

from dagster_graphql.schema.asset_condition_evaluations import get_expanded_label
from dagster_graphql.schema.util import non_null_list


class GrapheneAutomationCondition(graphene.ObjectType):
    label = graphene.Field(graphene.String)
    expandedLabel = non_null_list(graphene.String)

    class Meta:
        name = "AutomationCondition"

    def __init__(self, automation_condition: AutomationCondition):
        super().__init__(
            label=automation_condition.get_label(),
            expandedLabel=get_expanded_label(automation_condition),
        )
