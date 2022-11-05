import time
from unittest import mock

import pytest

from dagster._core.errors import (
    DagsterRepositoryLocationLoadError,
    DagsterRepositoryLocationNotFoundError,
)
from dagster._core.host_representation.origin import RegisteredRepositoryLocationOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import WorkspaceLocationEntry, WorkspaceLocationLoadStatus
from dagster._utils.error import SerializableErrorInfo


def test_get_repository_location():

    mock_loc = mock.MagicMock()

    error_info = SerializableErrorInfo(message="oopsie", stack=[], cls_name="Exception")

    context = WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            "loading_loc": WorkspaceLocationEntry(
                origin=RegisteredRepositoryLocationOrigin("loading_loc"),
                repository_location=None,
                load_error=None,
                load_status=WorkspaceLocationLoadStatus.LOADING,
                display_metadata={},
                update_timestamp=time.time(),
            ),
            "loaded_loc": WorkspaceLocationEntry(
                origin=RegisteredRepositoryLocationOrigin("loaded_loc"),
                repository_location=mock_loc,
                load_error=None,
                load_status=WorkspaceLocationLoadStatus.LOADED,
                display_metadata={},
                update_timestamp=time.time(),
            ),
            "error_loc": WorkspaceLocationEntry(
                origin=RegisteredRepositoryLocationOrigin("error_loc"),
                repository_location=None,
                load_error=error_info,
                load_status=WorkspaceLocationLoadStatus.LOADED,
                display_metadata={},
                update_timestamp=time.time(),
            ),
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )

    assert context.get_repository_location("loaded_loc") == mock_loc
    with pytest.raises(DagsterRepositoryLocationLoadError, match="oopsie"):
        context.get_repository_location("error_loc")

    with pytest.raises(
        DagsterRepositoryLocationNotFoundError, match="Location loading_loc is still loading"
    ):
        context.get_repository_location("loading_loc")

    with pytest.raises(
        DagsterRepositoryLocationNotFoundError,
        match="Location missing_loc does not exist in workspace",
    ):
        context.get_repository_location("missing_loc")
