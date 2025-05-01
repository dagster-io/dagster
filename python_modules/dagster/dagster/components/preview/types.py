from typing import TYPE_CHECKING, Any

from dagster_shared.record import record

from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.storage.components_storage.types import ComponentChange
from dagster._serdes import whitelist_for_serdes

# file contents for specific component
if TYPE_CHECKING:
    from dagster._core.definitions.selector import RepositorySelector


@whitelist_for_serdes
@record
class ComponentInstanceContentsRequest:
    repo_selector: "RepositorySelector"
    component_keys: list[str]


@whitelist_for_serdes
@record
class ComponentInstanceContents:
    component_key: str
    file_path: str
    file_contents: str


@whitelist_for_serdes
@record
class ComponentInstanceContentsResponse:
    contents: list[ComponentInstanceContents]


# preview after changes


@whitelist_for_serdes
@record
class ComponentInstancePreviewResponse:
    defs_snapshot: RepositorySnap


@whitelist_for_serdes
@record
class ComponentInstancePreviewRequest:
    repo_selector: "RepositorySelector"
    component_keys: list[str]
    preview_changes: list[ComponentChange]


# scaffold new component
@whitelist_for_serdes
@record
class ScaffoldedComponentInstancePreviewRequest:
    repo_selector: "RepositorySelector"
    component_type: str
    path: str
    scaffold_config: dict[str, Any]


@whitelist_for_serdes
@record
class ScaffoldedComponentInstancePreviewResponse:
    scaffolded_sha: str
