from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence

from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.host_representation import CodeLocation, CodeLocationOrigin


# For locations that are loaded asynchronously
class CodeLocationLoadStatus(Enum):
    LOADING = "LOADING"  # Waiting for location to load or update
    LOADED = "LOADED"  # Finished loading (may be an error)


class CodeLocationEntry(NamedTuple):
    origin: "CodeLocationOrigin"
    code_location: Optional["CodeLocation"]
    load_error: Optional[SerializableErrorInfo]
    load_status: CodeLocationLoadStatus
    display_metadata: Mapping[str, str]
    update_timestamp: float


class CodeLocationStatusEntry(NamedTuple):
    """Slimmer version of WorkspaceLocationEntry, containing the minimum set of information required
    to know whether the workspace needs reloading.
    """

    location_name: str
    load_status: CodeLocationLoadStatus
    update_timestamp: float


class IWorkspace(ABC):
    """Manages a set of CodeLocations."""

    @abstractmethod
    def get_code_location(self, location_name: str) -> "CodeLocation":
        """Return the CodeLocation for the given location name, or raise an error if there is an error loading it."""

    @abstractmethod
    def get_workspace_snapshot(self) -> Mapping[str, CodeLocationEntry]:
        """Return an entry for each location in the workspace."""

    @abstractmethod
    def get_code_location_statuses(self) -> Sequence[CodeLocationStatusEntry]:
        pass


def location_status_from_location_entry(
    entry: CodeLocationEntry,
) -> CodeLocationStatusEntry:
    return CodeLocationStatusEntry(
        location_name=entry.origin.location_name,
        load_status=entry.load_status,
        update_timestamp=entry.update_timestamp,
    )
