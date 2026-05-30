import graphene
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
    get_expanded_label,
)
from dagster._core.remote_representation.external_data import AssetNodeSnap

from dagster_graphql.schema.util import non_null_list


def get_ac_snapshot(snap: AssetNodeSnap) -> AutomationConditionSnapshot | None:
    raw = snap.automation_condition_snapshot or snap.automation_condition
    if raw is None:
        return None
    return raw if isinstance(raw, AutomationConditionSnapshot) else raw.get_snapshot()


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

    @staticmethod
    def to_manifest_dict(snap: AssetNodeSnap) -> dict | None:
        ac_snapshot = get_ac_snapshot(snap)
        if ac_snapshot is None:
            return None
        # Workspace consumers only check truthiness; `label` / `expandedLabel`
        # are read off the live AssetAutomationDataProvider query and per-asset
        # detail fragments, not the workspace path. Keep the manifest in sync
        # with the gql fragment (which only requests __typename).
        return {"__typename": "AutomationCondition"}
