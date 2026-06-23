import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from dagster_shared.record import record
from dagster_shared.serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster_shared.serdes.objects.package_entry import EnvRegistryKey
from dagster_shared.seven import load_module_object

from dagster._core.storage.defs_state.base import DefsStateStorage

if TYPE_CHECKING:
    from dagster.components.component.component import Component


def import_component_class(type_name: str) -> "type[Component]":
    """Import a Component class from a fully qualified type name."""
    from dagster.components.component.component import Component

    key = EnvRegistryKey.from_typename(type_name)
    obj = load_module_object(key.namespace, key.name)
    if not (isinstance(obj, type) and issubclass(obj, Component)):
        raise TypeError(f"{type_name} is not a Component subclass")
    return obj


@whitelist_for_serdes
@record
class AppManagedComponentEntry:
    """A single app-managed component, persisted at its own state key.

    ``attributes`` is the YAML source for the component's attributes block,
    stored verbatim so the editing UI can round-trip user input (including
    comments and key ordering).
    """

    component_type: str
    attributes: str


def get_app_managed_prefix(location_name: str) -> str:
    """The shared prefix for all app-managed component state keys at a location."""
    return f"dagster-app-managed-components[{location_name}]/"


def get_app_managed_component_state_key(location_name: str, component_id: str) -> str:
    return f"{get_app_managed_prefix(location_name)}{component_id}"


def get_app_managed_component_ids(storage: DefsStateStorage, location_name: str) -> set[str]:
    """Discover all UI components for a location.

    Delegates to ``DefsStateStorage.list_state_keys_with_prefix`` and
    slices the prefix off each returned key. The default storage
    implementation does the filter in memory; backends that grow large
    enough to care can override the listing primitive directly.
    """
    prefix = get_app_managed_prefix(location_name)
    return {k[len(prefix) :] for k in storage.list_state_keys_with_prefix(prefix)}


def read_app_managed_component_entry_at_version(
    storage: DefsStateStorage, location_name: str, component_id: str, version: str
) -> AppManagedComponentEntry:
    """Read the bytes for a specific version of a UI component entry."""
    key = get_app_managed_component_state_key(location_name, component_id)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "entry"
        storage.download_state_to_path(key, version, path)
        return deserialize_value(path.read_text(encoding="utf-8"), as_type=AppManagedComponentEntry)


def read_app_managed_component_entry(
    storage: DefsStateStorage, location_name: str, component_id: str
) -> AppManagedComponentEntry | None:
    """Read the latest UI component entry. Returns ``None`` if no version exists.

    Resolves the version against ``DefsStateStorage`` directly, so this
    reflects whatever is most recently written to storage. Callers that need
    a version pinned to the current ``DefinitionsLoadContext`` (e.g. component
    tree loads) should resolve the version themselves and use
    ``read_app_managed_component_entry_at_version``.
    """
    key = get_app_managed_component_state_key(location_name, component_id)
    version = storage.get_latest_version(key)
    if version is None:
        return None
    return read_app_managed_component_entry_at_version(
        storage, location_name, component_id, version
    )


def write_app_managed_component_entry(
    storage: DefsStateStorage,
    location_name: str,
    component_id: str,
    entry: AppManagedComponentEntry,
) -> str:
    """Write (or overwrite) a UI component entry. Returns the new version.

    No optimistic-concurrency check: writes are last-writer-wins. Two
    concurrent writers targeting *different* component_ids don't contend
    because they target different keys; two writers targeting the same
    component_id silently resolve to whichever finishes last.
    """
    key = get_app_managed_component_state_key(location_name, component_id)
    new_version = str(uuid4())
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "entry"
        path.write_text(serialize_value(entry), encoding="utf-8")
        storage.upload_state_from_path(key, new_version, path)
    return new_version


def delete_app_managed_component_entry(
    storage: DefsStateStorage,
    location_name: str,
    component_id: str,
) -> None:
    """Delete a UI component entry.

    Idempotent — deleting a component_id that doesn't exist is a no-op.
    The next ``get_app_managed_component_ids`` call for this location will not
    include the deleted id, and the ``ComponentTree``'s next
    ``find_root_decl`` call will exclude it from the tree.
    """
    storage.set_latest_version(
        get_app_managed_component_state_key(location_name, component_id), None
    )
