from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Dict, NamedTuple, Optional

from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.host_representation import RepositoryLocation, RepositoryLocationOrigin

# For locations that are loaded asynchronously
class WorkspaceLocationLoadStatus(Enum):
    LOADING = "LOADING"  # Waiting for location to load or update
    LOADED = "LOADED"  # Finished loading (may be an error)


class WorkspaceLocationEntry(NamedTuple):
    origin: "RepositoryLocationOrigin"
    repository_location: Optional["RepositoryLocation"]
    load_error: Optional[SerializableErrorInfo]
    load_status: WorkspaceLocationLoadStatus
    display_metadata: Dict[str, str]
    update_timestamp: float


class IWorkspace(ABC):
    """
    Manages a set of RepositoryLocations.
    """

    @abstractmethod
    def get_repository_location(self, location_name: str) -> "RepositoryLocation":
        """Return the RepositoryLocation for the given location name, or raise an error if there is an error loading it."""

    @abstractmethod
    def get_workspace_snapshot(self) -> Dict[str, WorkspaceLocationEntry]:
        """Return an entry for each location in the workspace."""
