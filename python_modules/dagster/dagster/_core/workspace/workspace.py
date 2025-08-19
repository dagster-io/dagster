from collections.abc import Mapping
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Optional

from dagster._record import ImportFrom, record
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
    from dagster._core.remote_origin import CodeLocationOrigin
    from dagster._core.remote_representation.code_location import CodeLocation


# For locations that are loaded asynchronously
class CodeLocationLoadStatus(Enum):
    LOADING = "LOADING"  # Waiting for location to load or update
    LOADED = "LOADED"  # Finished loading (may be an error)


@record
class CodeLocationEntry:
    origin: Annotated[
        "CodeLocationOrigin",
        ImportFrom("dagster._core.remote_origin"),
    ]
    code_location: Optional[
        Annotated[
            "CodeLocation",
            ImportFrom("dagster._core.remote_representation.code_location"),
        ]
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
class CurrentWorkspace:
    code_location_entries: Mapping[str, CodeLocationEntry]

    @cached_property
    def asset_graph(self) -> "RemoteWorkspaceAssetGraph":
        from dagster._core.definitions.assets.graph.remote_asset_graph import (
            RemoteWorkspaceAssetGraph,
        )

        return RemoteWorkspaceAssetGraph.build(self)

    def with_code_location(self, name: str, entry: CodeLocationEntry) -> "CurrentWorkspace":
        return CurrentWorkspace(code_location_entries={**self.code_location_entries, name: entry})


def location_status_from_location_entry(
    entry: CodeLocationEntry,
) -> CodeLocationStatusEntry:
    return CodeLocationStatusEntry(
        location_name=entry.origin.location_name,
        load_status=entry.load_status,
        update_timestamp=entry.update_timestamp,
        version_key=entry.version_key,
    )
