from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence, Tuple

from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
    from dagster._core.remote_representation import CodeLocation, CodeLocationOrigin
    from dagster._core.remote_representation.external_data import (
        ExternalAssetCheck,
        ExternalAssetNode,
    )
    from dagster._core.remote_representation.handle import RepositoryHandle


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

    @cached_property
    def asset_graph(self) -> "RemoteAssetGraph":
        """Returns a workspace scoped RemoteAssetGraph."""
        from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph

        code_locations = (
            location_entry.code_location
            for location_entry in self.get_workspace_snapshot().values()
            if location_entry.code_location
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in code_location.get_repositories().values()
        )
        repo_handle_external_asset_nodes: Sequence[
            Tuple["RepositoryHandle", "ExternalAssetNode"]
        ] = []
        asset_checks: Sequence["ExternalAssetCheck"] = []

        for repo in repos:
            for external_asset_node in repo.get_external_asset_nodes():
                repo_handle_external_asset_nodes.append((repo.handle, external_asset_node))

            asset_checks.extend(repo.get_external_asset_checks())

        return RemoteAssetGraph.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=repo_handle_external_asset_nodes,
            external_asset_checks=asset_checks,
        )


def location_status_from_location_entry(
    entry: CodeLocationEntry,
) -> CodeLocationStatusEntry:
    return CodeLocationStatusEntry(
        location_name=entry.origin.location_name,
        load_status=entry.load_status,
        update_timestamp=entry.update_timestamp,
    )
