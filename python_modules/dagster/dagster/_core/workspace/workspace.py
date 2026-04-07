import threading
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Annotated

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


class DefinitionsSource(Enum):
    CODE_SERVER = "CODE_SERVER"
    CONNECTION = "CONNECTION"


@record
class CodeLocationEntry:
    origin: Annotated[
        "CodeLocationOrigin",
        ImportFrom("dagster._core.remote_origin"),
    ]
    code_location: (
        Annotated["CodeLocation", ImportFrom("dagster._core.remote_representation.code_location")]
        | None
    )
    load_error: SerializableErrorInfo | None
    load_status: CodeLocationLoadStatus
    display_metadata: Mapping[str, str]
    update_timestamp: float
    version_key: str
    definitions_source: DefinitionsSource


@record
class CodeLocationStatusEntry:
    """Slimmer version of WorkspaceLocationEntry, containing the minimum set of information required
    to know whether the workspace needs reloading.
    """

    location_name: str
    load_status: CodeLocationLoadStatus
    update_timestamp: float
    version_key: str
    has_load_error: bool


class CurrentWorkspace:
    def __init__(self, code_location_entries: Mapping[str, CodeLocationEntry]):
        self.code_location_entries = code_location_entries
        self._asset_graph_lock = threading.Lock()
        self._asset_graph: RemoteWorkspaceAssetGraph | None = None

    @property
    def asset_graph(self) -> "RemoteWorkspaceAssetGraph":
        if self._asset_graph is not None:
            return self._asset_graph

        from dagster._core.definitions.assets.graph.remote_asset_graph import (
            RemoteWorkspaceAssetGraph,
        )

        # building the full asset graph is expensive - so ensure at most one
        # thread is doing that work at once, and subsequent threads reuse the result
        with self._asset_graph_lock:
            if self._asset_graph is not None:
                return self._asset_graph
            self._asset_graph = RemoteWorkspaceAssetGraph.build(self)
            return self._asset_graph

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
        has_load_error=entry.load_error is not None,
    )
