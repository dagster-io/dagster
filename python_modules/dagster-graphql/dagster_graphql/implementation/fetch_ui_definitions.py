from typing import TYPE_CHECKING

from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.workspace.permissions import Permissions
from dagster.components.component.ui_definitions_state import (
    UIComponentEntry,
    delete_ui_component_entry,
    get_ui_component_ids,
    read_ui_component_entry,
    write_ui_component_entry,
)

from dagster_graphql.implementation.utils import assert_permission_for_location

if TYPE_CHECKING:
    from dagster._core.storage.defs_state.base import DefsStateStorage

    from dagster_graphql.schema.ui_definitions import (
        GrapheneDeleteUIComponentSuccess,
        GrapheneSetUIComponentSuccess,
        GrapheneUIComponents,
    )
    from dagster_graphql.schema.util import ResolveInfo


def _require_storage(graphene_info: "ResolveInfo") -> "DefsStateStorage":
    storage = graphene_info.context.instance.defs_state_storage
    if storage is None:
        raise DagsterInvariantViolationError(
            "DefsStateStorage is not configured on this instance — UI-defined components"
            " require a defs state storage."
        )
    return storage


def _to_graphene_component(component_id: str, entry: UIComponentEntry):
    from dagster_graphql.schema.ui_definitions import GrapheneUIComponent

    return GrapheneUIComponent(
        componentId=component_id,
        componentType=entry.component_type,
        attributes=entry.attributes,
    )


def get_ui_components_for_location(
    graphene_info: "ResolveInfo", location_name: str
) -> "GrapheneUIComponents":
    from dagster_graphql.schema.ui_definitions import GrapheneUIComponents

    storage = _require_storage(graphene_info)
    components = []
    for component_id in sorted(get_ui_component_ids(storage, location_name)):
        entry = read_ui_component_entry(storage, location_name, component_id)
        if entry is None:
            # Concurrent delete between listing and reading — skip.
            continue
        components.append(_to_graphene_component(component_id, entry))
    return GrapheneUIComponents(locationName=location_name, components=components)


def set_ui_component(
    graphene_info: "ResolveInfo",
    location_name: str,
    component_id: str,
    component_type: str,
    attributes: str,
) -> "GrapheneSetUIComponentSuccess":
    from dagster_graphql.schema.ui_definitions import GrapheneSetUIComponentSuccess

    assert_permission_for_location(graphene_info, Permissions.EDIT_UI_DEFINITIONS, location_name)
    storage = _require_storage(graphene_info)
    entry = UIComponentEntry(component_type=component_type, attributes=attributes)
    write_ui_component_entry(storage, location_name, component_id, entry)
    return GrapheneSetUIComponentSuccess(component=_to_graphene_component(component_id, entry))


def delete_ui_component(
    graphene_info: "ResolveInfo", location_name: str, component_id: str
) -> "GrapheneDeleteUIComponentSuccess":
    from dagster_graphql.schema.ui_definitions import GrapheneDeleteUIComponentSuccess

    assert_permission_for_location(graphene_info, Permissions.EDIT_UI_DEFINITIONS, location_name)
    storage = _require_storage(graphene_info)
    delete_ui_component_entry(storage, location_name, component_id)
    return GrapheneDeleteUIComponentSuccess(locationName=location_name, componentId=component_id)
