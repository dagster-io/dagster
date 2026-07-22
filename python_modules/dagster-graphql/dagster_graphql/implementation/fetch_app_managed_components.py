from typing import TYPE_CHECKING, Union

from dagster._core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterUserCodeUnreachableTimeoutError,
)
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
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external_data import ComponentInstanceSnap
    from dagster._core.storage.defs_state.base import DefsStateStorage
    from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

    from dagster_graphql.schema.app_managed_components import (
        GrapheneAppManagedComponents,
        GrapheneComponent,
        GrapheneComponents,
        GrapheneDeleteAppManagedComponentSuccess,
        GrapheneRefreshComponentStateAccepted,
        GrapheneRefreshComponentStateError,
        GrapheneRefreshComponentStateSuccess,
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
    graphene_info.context.reload_code_location_with_latest_defs_state(location_name)
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
    graphene_info.context.reload_code_location_with_latest_defs_state(location_name)
    return GrapheneDeleteAppManagedComponentSuccess(
        locationName=location_name, componentId=component_id
    )


def _component_snap_to_graphene(
    snap: "ComponentInstanceSnap",
    *,
    attributes: str | None,
    defs_state_info: "DefsStateInfo | None",
) -> "GrapheneComponent":
    from dagster_graphql.schema.app_managed_components import GrapheneComponent
    from dagster_graphql.schema.external import GrapheneDefsKeyStateInfo

    key_info = None
    if snap.defs_state_key and defs_state_info is not None:
        info = defs_state_info.info_mapping.get(snap.defs_state_key)
        if info is not None:
            key_info = GrapheneDefsKeyStateInfo(
                info.version, info.create_timestamp, info.management_type
            )

    return GrapheneComponent(
        componentId=snap.key,
        componentType=snap.full_type_name,
        isAppManaged=bool(snap.is_ui_defined),
        attributes=attributes,
        defsStateKey=snap.defs_state_key,
        defsStateManagementType=snap.defs_state_management_type,
        defsStateInfo=key_info,
    )


def _live_defs_state_info(
    code_location: "CodeLocation", storage: "DefsStateStorage | None"
) -> "DefsStateInfo | None":
    """Overlay storage's live state info on top of the code location's cached
    snapshot. Storage is authoritative for ``VERSIONED_STATE_STORAGE`` keys, so
    polling sees the new version as soon as a refresh writes it — without
    forcing a code location reload on every poll. The cached snapshot covers
    ``LOCAL_FILESYSTEM`` / ``LEGACY_CODE_SERVER_SNAPSHOTS`` keys that storage
    doesn't track.
    """
    from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

    cached = code_location.get_defs_state_info()
    if storage is None:
        return cached
    live = storage.get_latest_defs_state_info()
    if live is None:
        return cached
    if cached is None:
        return live
    return DefsStateInfo(info_mapping={**cached.info_mapping, **live.info_mapping})


def get_components_for_location(
    graphene_info: "ResolveInfo", location_name: str
) -> "GrapheneComponents":
    """Flat list of every component in a code location's component tree —
    both file-based and app-managed.
    """
    from dagster_graphql.schema.app_managed_components import GrapheneComponents

    workspace = graphene_info.context.get_current_workspace()
    location_entry = workspace.code_location_entries.get(location_name)
    if location_entry is None or location_entry.code_location is None:
        return GrapheneComponents(locationName=location_name, components=[])

    code_location = location_entry.code_location
    storage = graphene_info.context.instance.defs_state_storage
    defs_state_info = _live_defs_state_info(code_location, storage)
    app_managed_attrs_by_id: dict[str, str] = {}
    if storage is not None:
        for cid in get_app_managed_component_ids(storage, location_name):
            entry = read_app_managed_component_entry(storage, location_name, cid)
            if entry is not None:
                app_managed_attrs_by_id[cid] = entry.attributes

    components: list[GrapheneComponent] = []
    for repo in code_location.get_repositories().values():
        component_tree = repo.repository_snap.component_tree
        if component_tree is None:
            continue
        for snap in component_tree.leaf_instances:
            attributes = app_managed_attrs_by_id.get(snap.key) if snap.is_ui_defined else None
            components.append(
                _component_snap_to_graphene(
                    snap,
                    attributes=attributes,
                    defs_state_info=defs_state_info,
                )
            )
    return GrapheneComponents(locationName=location_name, components=components)


def refresh_component_state(
    graphene_info: "ResolveInfo", location_name: str, defs_state_key: str
) -> Union[
    "GrapheneRefreshComponentStateSuccess",
    "GrapheneRefreshComponentStateAccepted",
    "GrapheneRefreshComponentStateError",
]:
    """Refresh state for one state-backed component, with three outcomes.

    - Success: gRPC reply arrived within the sync-wait window; return the
      refreshed component.
    - Accepted: sync-wait elapsed first; refresh is still running and callers
      should poll ``componentsForLocation`` for ``defsStateInfo.version`` to
      change.
    - Error: gRPC reply arrived but reported failure (e.g. external API
      outage); surfaces the rich message from user code.
    """
    from dagster_graphql.schema.app_managed_components import (
        GrapheneRefreshComponentStateAccepted,
        GrapheneRefreshComponentStateError,
        GrapheneRefreshComponentStateSuccess,
    )

    assert_permission_for_location(
        graphene_info, Permissions.REFRESH_COMPONENT_STATE, location_name
    )
    try:
        graphene_info.context.refresh_component_state(location_name, [defs_state_key])
    except DagsterUserCodeUnreachableTimeoutError:
        return GrapheneRefreshComponentStateAccepted(
            locationName=location_name,
            defsStateKey=defs_state_key,
        )
    except DagsterError as e:
        return GrapheneRefreshComponentStateError(
            locationName=location_name,
            defsStateKey=defs_state_key,
            message=str(e),
        )
    new_request_context = graphene_info.context.reload_code_location(location_name)
    location_entry = new_request_context.get_location_entry(location_name)
    code_location = location_entry.code_location if location_entry else None
    if code_location is None:
        raise DagsterInvariantViolationError(
            f"Code location '{location_name}' is not loaded after refresh."
        )

    defs_state_info = code_location.get_defs_state_info()
    for repo in code_location.get_repositories().values():
        component_tree = repo.repository_snap.component_tree
        if component_tree is None:
            continue
        for snap in component_tree.leaf_instances:
            if snap.defs_state_key == defs_state_key:
                return GrapheneRefreshComponentStateSuccess(
                    component=_component_snap_to_graphene(
                        snap, attributes=None, defs_state_info=defs_state_info
                    )
                )
    raise DagsterInvariantViolationError(
        f"No component with defs state key '{defs_state_key}' found in location '{location_name}' "
        "after refresh."
    )
