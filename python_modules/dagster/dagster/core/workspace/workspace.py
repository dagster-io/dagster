from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, NamedTuple, Optional

from dagster.core.host_representation import RepositoryLocation, RepositoryLocationOrigin
from dagster.utils.error import SerializableErrorInfo


class IWorkspace(ABC):
    """
    A class that knows how to get a RepositoryLocation from a RepositoryLocationOrigin,
    possibly creating it lazily.

    Used both by Dagit (where this is a fixed WorkspaceRequestContext that manages a static
    list of RepositoryLocations) and the dagster-daemon process in, which lazily creates and reloads
    repository locations in a DynamicWorkspace based on the running schedules, sensors, and queued
    runs in the database.
    """

    @abstractmethod
    def get_location(self, origin: RepositoryLocationOrigin):
        """Return the RepositoryLocation for the given RepositoryLocationOrigin, or raise an error if there is an error loading it."""


# For locations that are loaded asynchronously
class WorkspaceLocationLoadStatus(Enum):
    LOADING = "LOADING"  # Waiting for location to load or update
    LOADED = "LOADED"  # Finished loading (may be an error)


class WorkspaceLocationEntry(NamedTuple):
    origin: RepositoryLocationOrigin
    repository_location: Optional[RepositoryLocation]
    load_error: Optional[SerializableErrorInfo]
    load_status: WorkspaceLocationLoadStatus
    display_metadata: Dict[str, str]
    update_timestamp: float
