import json
from typing import TYPE_CHECKING, Any, Union

import yaml
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
from dagster.components.core.load_defs import get_plugin_component_jsons_for_code_location
from dagster_shared.yaml_utils import safe_load_yaml

from dagster_graphql.implementation.utils import assert_permission_for_location

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external_data import ComponentInstanceSnap
    from dagster._core.storage.defs_state.base import DefsStateStorage
    from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

    from dagster_graphql.schema.app_managed_components import (
        GrapheneAppManagedComponents,
        GrapheneAppManagedComponentValidationError,
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


def _resolve_ref(node: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    ref = node.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return node
    current: Any = root
    for segment in ref[2:].split("/"):
        if not isinstance(current, dict):
            return node
        current = current.get(segment)
    return current if isinstance(current, dict) else node


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _collect_required_field_errors(
    *, schema_node: Any, data: Any, root: dict[str, Any], path: str, errors: list[str]
) -> None:
    """Server-side port of the frontend ``validate.ts`` required-field walker.

    Verifies required fields are present and non-empty, recursing into objects
    and treating an ``anyOf``/``oneOf`` as satisfied when any variant validates.
    Deliberately narrow and lenient on types: it runs against the *raw* schema,
    whose fields carry the injectable ``| str`` escape-hatch variant, so nothing
    that would actually load is rejected. Deeper type validation stays with the
    component model at load time, where full reference validation happens.
    """
    if not isinstance(schema_node, dict):
        return
    node = _resolve_ref(schema_node, root)

    for key in ("anyOf", "oneOf"):
        variants = node.get(key)
        if isinstance(variants, list) and variants:
            for variant in variants:
                variant_errors: list[str] = []
                _collect_required_field_errors(
                    schema_node=variant,
                    data=data,
                    root=root,
                    path=path,
                    errors=variant_errors,
                )
                if not variant_errors:
                    return
            errors.append(f"{path or '<root>'}: does not match any allowed schema variant")
            return

    required = node.get("required")
    properties = node.get("properties")
    if isinstance(required, list) and isinstance(properties, dict):
        if not isinstance(data, dict):
            errors.append(f"{path or '<root>'}: expected a mapping")
            return
        for name in required:
            if not isinstance(name, str):
                continue
            child_path = f"{path}.{name}" if path else name
            if _is_missing(data.get(name)):
                errors.append(f"{child_path}: required field is missing")
                continue
            _collect_required_field_errors(
                schema_node=properties.get(name),
                data=data.get(name),
                root=root,
                path=child_path,
                errors=errors,
            )


def _validate_app_managed_attributes(
    graphene_info: "ResolveInfo", location_name: str, component_type: str, attributes: str
) -> list[str]:
    """Validate authored attributes before persisting, returning error messages.

    Catches the failures that today only surface on reload: malformed YAML, a
    component type unknown to the location, and missing required fields. No
    user-code execution — validates against the component type's schema already
    available in the host.
    """
    try:
        parsed = safe_load_yaml(attributes) if attributes.strip() else {}
    except yaml.YAMLError as e:
        return [f"Attributes are not valid YAML: {e}"]
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        return ["Attributes must be a YAML mapping."]

    context = graphene_info.context
    if not context.has_code_location(location_name):
        # Location isn't loaded, so we can't resolve the schema here; let the
        # reload path validate rather than blocking on a transient state.
        return []
    code_location = context.get_code_location(location_name)

    schema: Any = None
    type_found = False
    for _namespace, component_json in get_plugin_component_jsons_for_code_location(code_location):
        if component_json.get("name") == component_type:
            type_found = True
            raw_schema = component_json.get("schema")
            if isinstance(raw_schema, str):
                try:
                    schema = json.loads(raw_schema)
                except json.JSONDecodeError:
                    schema = None
            elif isinstance(raw_schema, dict):
                schema = raw_schema
            break

    if not type_found:
        return [f"Unknown component type '{component_type}' in location '{location_name}'."]
    if not isinstance(schema, dict):
        return []

    errors: list[str] = []
    _collect_required_field_errors(
        schema_node=schema, data=parsed, root=schema, path="", errors=errors
    )
    return errors


def set_app_managed_component(
    graphene_info: "ResolveInfo",
    location_name: str,
    component_id: str,
    component_type: str,
    attributes: str,
) -> "GrapheneSetAppManagedComponentSuccess | GrapheneAppManagedComponentValidationError":
    from dagster_graphql.schema.app_managed_components import (
        GrapheneAppManagedComponentValidationError,
        GrapheneSetAppManagedComponentSuccess,
    )

    assert_permission_for_location(
        graphene_info, Permissions.EDIT_APP_MANAGED_COMPONENTS, location_name
    )

    if not graphene_info.context.app_managed_component_write_allowed():
        return GrapheneAppManagedComponentValidationError(
            componentId=component_id,
            message=(
                "Editing components directly is disabled for production deployments."
                " Open a pull request to change production."
            ),
            errors=["Live component writes are only permitted on branch deployments."],
        )

    validation_errors = _validate_app_managed_attributes(
        graphene_info, location_name, component_type, attributes
    )
    if validation_errors:
        return GrapheneAppManagedComponentValidationError(
            componentId=component_id,
            message="Component attributes failed validation and were not saved.",
            errors=validation_errors,
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
        isAppManaged=bool(snap.app_managed),
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
            attributes = app_managed_attrs_by_id.get(snap.key) if snap.app_managed else None
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
