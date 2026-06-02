from typing import TYPE_CHECKING

from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.workspace.permissions import Permissions
from dagster.components.component.app_managed_state import (
    AppManagedComponentEntry,
    delete_app_managed_component_entry,
    get_app_managed_component_ids,
    read_app_managed_component_entry,
    write_app_managed_component_entry,
)

from dagster_graphql.implementation.utils import assert_permission_for_location

if TYPE_CHECKING:
    from dagster._core.storage.defs_state.base import DefsStateStorage

    from dagster_graphql.schema.app_managed_components import (
        GrapheneAppManagedComponents,
        GrapheneDeleteAppManagedComponentSuccess,
        GrapheneSetAppManagedComponentSuccess,
    )
    from dagster_graphql.schema.util import ResolveInfo


def _require_storage(graphene_info: "ResolveInfo") -> "DefsStateStorage":
    storage = graphene_info.context.instance.defs_state_storage
    if storage is None:
        raise DagsterInvariantViolationError(
            "DefsStateStorage is not configured on this instance — app-managed components"
            " require a defs state storage."
        )
    return storage


def _to_graphene_component(component_id: str, entry: AppManagedComponentEntry):
    from dagster_graphql.schema.app_managed_components import GrapheneAppManagedComponent

    return GrapheneAppManagedComponent(
        componentId=component_id,
        componentType=entry.component_type,
        attributes=entry.attributes,
    )


def get_app_managed_components_for_location(
    graphene_info: "ResolveInfo", location_name: str
) -> "GrapheneAppManagedComponents":
    from dagster_graphql.schema.app_managed_components import GrapheneAppManagedComponents

    storage = _require_storage(graphene_info)
    components = []
    for component_id in sorted(get_app_managed_component_ids(storage, location_name)):
        entry = read_app_managed_component_entry(storage, location_name, component_id)
        if entry is None:
            # Concurrent delete between listing and reading — skip.
            continue
        components.append(_to_graphene_component(component_id, entry))
    return GrapheneAppManagedComponents(locationName=location_name, components=components)


def set_app_managed_component(
    graphene_info: "ResolveInfo",
    location_name: str,
    component_id: str,
    component_type: str,
    attributes: str,
) -> "GrapheneSetAppManagedComponentSuccess":
    from dagster_graphql.schema.app_managed_components import GrapheneSetAppManagedComponentSuccess

    assert_permission_for_location(
        graphene_info, Permissions.EDIT_APP_MANAGED_COMPONENTS, location_name
    )
    storage = _require_storage(graphene_info)
    entry = AppManagedComponentEntry(component_type=component_type, attributes=attributes)
    write_app_managed_component_entry(storage, location_name, component_id, entry)
    graphene_info.context.reload_code_location(location_name)
    return GrapheneSetAppManagedComponentSuccess(
        component=_to_graphene_component(component_id, entry)
    )


def delete_app_managed_component(
    graphene_info: "ResolveInfo", location_name: str, component_id: str
) -> "GrapheneDeleteAppManagedComponentSuccess":
    from dagster_graphql.schema.app_managed_components import (
        GrapheneDeleteAppManagedComponentSuccess,
    )

    assert_permission_for_location(
        graphene_info, Permissions.EDIT_APP_MANAGED_COMPONENTS, location_name
    )
    storage = _require_storage(graphene_info)
    delete_app_managed_component_entry(storage, location_name, component_id)
    graphene_info.context.reload_code_location(location_name)
    return GrapheneDeleteAppManagedComponentSuccess(
        locationName=location_name, componentId=component_id
    )
