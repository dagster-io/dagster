from enum import Enum
from typing import TYPE_CHECKING

from dagster._record import record
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.selector import RepositorySelector


@whitelist_for_serdes
class ComponentChangeOperation(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@whitelist_for_serdes
@record(kw_only=False)
class ComponentKey:
    path: list[str]


@whitelist_for_serdes
@record
class ComponentChange:
    component_key: ComponentKey
    repository_selector: "RepositorySelector"
    file_path: list[str]
    operation: ComponentChangeOperation
    snapshot_sha: str
