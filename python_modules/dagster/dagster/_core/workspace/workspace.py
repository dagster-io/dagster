from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Tuple

from typing_extensions import Annotated

from dagster._record import ImportFrom, record
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


@record
class CodeLocationEntry:
    origin: Annotated["CodeLocationOrigin", ImportFrom("dagster._core.remote_representation")]
    code_location: Optional[
        Annotated["CodeLocation", ImportFrom("dagster._core.remote_representation")]
    ]
    load_error: Optional[SerializableErrorInfo]
    load_status: CodeLocationLoadStatus
    display_metadata: Mapping[str, str]
    update_timestamp: float
    version_key: str


@record
class CodeLocationStatusEntry:
    """Slimmer version of WorkspaceLocationEntry, containing the minimum set of information required
    to know whether the workspace needs reloading.
    """

    location_name: str
    load_status: CodeLocationLoadStatus
    update_timestamp: float
    version_key: str


@record
class WorkspaceSnapshot:
    code_location_entries: Mapping[str, CodeLocationEntry]

    @cached_property
    def asset_graph(self) -> "RemoteAssetGraph":
        from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph

        code_locations = (
            location_entry.code_location
            for location_entry in self.code_location_entries.values()
            if location_entry.code_location
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in code_location.get_repositories().values()
        )
        repo_handle_assets: Sequence[Tuple["RepositoryHandle", "ExternalAssetNode"]] = []
        repo_handle_asset_checks: Sequence[Tuple["RepositoryHandle", "ExternalAssetCheck"]] = []

        for repo in repos:
            for external_asset_node in repo.get_external_asset_nodes():
                repo_handle_assets.append((repo.handle, external_asset_node))
            for external_asset_check in repo.get_external_asset_checks():
                repo_handle_asset_checks.append((repo.handle, external_asset_check))

        return RemoteAssetGraph.from_repository_handles_and_external_asset_nodes(
            repo_handle_assets=repo_handle_assets,
            repo_handle_asset_checks=repo_handle_asset_checks,
        )

    def with_code_location(self, name: str, entry: CodeLocationEntry) -> "WorkspaceSnapshot":
        return WorkspaceSnapshot(code_location_entries={**self.code_location_entries, name: entry})


def location_status_from_location_entry(
    entry: CodeLocationEntry,
) -> CodeLocationStatusEntry:
    return CodeLocationStatusEntry(
        location_name=entry.origin.location_name,
        load_status=entry.load_status,
        update_timestamp=entry.update_timestamp,
        version_key=entry.version_key,
    )
