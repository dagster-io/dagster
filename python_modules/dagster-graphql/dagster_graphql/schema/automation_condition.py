from collections.abc import Callable, Sequence

import graphene
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
    get_expanded_label,
)
from dagster._core.remote_representation.external_data import AssetNodeSnap

from dagster_graphql.schema.util import non_null_list


def snapshot_from_raw(
    raw: AutomationCondition | AutomationConditionSnapshot,
) -> AutomationConditionSnapshot:
    return raw if isinstance(raw, AutomationConditionSnapshot) else raw.get_snapshot()


def get_ac_snapshot(snap: AssetNodeSnap) -> AutomationConditionSnapshot | None:
    raw = snap.automation_condition_snapshot or snap.automation_condition
    return None if raw is None else snapshot_from_raw(raw)


class GrapheneAutomationCondition(graphene.ObjectType):
    label = graphene.Field(graphene.String)
    expandedLabel = non_null_list(graphene.String)

    class Meta:
        name = "AutomationCondition"

    def __init__(self, get_snapshot: Callable[[], AutomationConditionSnapshot]):
        # Building a snapshot and its expanded label both walk the whole condition tree, so
        # defer them until label/expandedLabel are requested; the common `{ __typename }`
        # query never pays for either.
        self._get_snapshot = get_snapshot
        self._snapshot: AutomationConditionSnapshot | None = None
        super().__init__()

    def _snapshot_once(self) -> AutomationConditionSnapshot:
        if self._snapshot is None:
            self._snapshot = self._get_snapshot()
        return self._snapshot

    def resolve_label(self, _graphene_info) -> str | None:
        return self._snapshot_once().node_snapshot.label

    def resolve_expandedLabel(self, _graphene_info) -> Sequence[str]:
        return get_expanded_label(self._snapshot_once())

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
