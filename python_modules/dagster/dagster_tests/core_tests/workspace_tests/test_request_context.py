import time
from unittest import mock

import pytest
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterCodeLocationNotFoundError,
)
from dagster._core.host_representation.origin import RegisteredCodeLocationOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
)
from dagster._utils.error import SerializableErrorInfo


def test_get_code_location():
    mock_loc = mock.MagicMock()

    error_info = SerializableErrorInfo(message="oopsie", stack=[], cls_name="Exception")

    context = WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            "loading_loc": CodeLocationEntry(
                origin=RegisteredCodeLocationOrigin("loading_loc"),
                code_location=None,
                load_error=None,
                load_status=CodeLocationLoadStatus.LOADING,
                display_metadata={},
                update_timestamp=time.time(),
            ),
            "loaded_loc": CodeLocationEntry(
                origin=RegisteredCodeLocationOrigin("loaded_loc"),
                code_location=mock_loc,
                load_error=None,
                load_status=CodeLocationLoadStatus.LOADED,
                display_metadata={},
                update_timestamp=time.time(),
            ),
            "error_loc": CodeLocationEntry(
                origin=RegisteredCodeLocationOrigin("error_loc"),
                code_location=None,
                load_error=error_info,
                load_status=CodeLocationLoadStatus.LOADED,
                display_metadata={},
                update_timestamp=time.time(),
            ),
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )

    assert context.get_code_location("loaded_loc") == mock_loc
    with pytest.raises(DagsterCodeLocationLoadError, match="oopsie"):
        context.get_code_location("error_loc")

    with pytest.raises(
        DagsterCodeLocationNotFoundError, match="Location loading_loc is still loading"
    ):
        context.get_code_location("loading_loc")

    with pytest.raises(
        DagsterCodeLocationNotFoundError,
        match="Location missing_loc does not exist in workspace",
    ):
        context.get_code_location("missing_loc")
