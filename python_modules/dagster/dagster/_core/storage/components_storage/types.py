from dagster import RepositorySelector
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster.components.preview.types import ComponentChangeOperation


@record
@whitelist_for_serdes
class ComponentKey:
    path: list[str]


@record
@whitelist_for_serdes
class ComponentChange:
    component_key: ComponentKey
    repository_selector: RepositorySelector
    file_path: list[str]
    operation: ComponentChangeOperation
    snapshot_sha: str
