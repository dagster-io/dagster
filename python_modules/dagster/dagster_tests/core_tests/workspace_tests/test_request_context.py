import time
from typing import Mapping
from unittest import mock

import pytest
from dagster._core.errors import DagsterCodeLocationLoadError, DagsterCodeLocationNotFoundError
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.feature_flags import (
    CodeLocationFeatureFlags,
    get_feature_flags_for_location,
)
from dagster._core.remote_representation.origin import RegisteredCodeLocationOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    WorkspaceSnapshot,
)
from dagster._utils.error import SerializableErrorInfo


@pytest.fixture
def workspace_request_context() -> WorkspaceRequestContext:
    mock_loc = mock.MagicMock(spec=CodeLocation)

    error_info = SerializableErrorInfo(message="oopsie", stack=[], cls_name="Exception")
    now = time.time()
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot=WorkspaceSnapshot(
            code_location_entries={
                "loading_loc": CodeLocationEntry(
                    origin=RegisteredCodeLocationOrigin("loading_loc"),
                    code_location=None,
                    load_error=None,
                    load_status=CodeLocationLoadStatus.LOADING,
                    display_metadata={},
                    update_timestamp=now,
                    version_key=str(now),
                ),
                "loaded_loc": CodeLocationEntry(
                    origin=RegisteredCodeLocationOrigin("loaded_loc"),
                    code_location=mock_loc,
                    load_error=None,
                    load_status=CodeLocationLoadStatus.LOADED,
                    display_metadata={},
                    update_timestamp=now,
                    version_key=str(now),
                ),
                "error_loc": CodeLocationEntry(
                    origin=RegisteredCodeLocationOrigin("error_loc"),
                    code_location=None,
                    load_error=error_info,
                    load_status=CodeLocationLoadStatus.LOADED,
                    display_metadata={},
                    update_timestamp=now,
                    version_key=str(now),
                ),
            }
        ),
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def test_get_code_location(workspace_request_context):
    context = workspace_request_context
    assert context.get_code_location("loaded_loc")
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


def _location_with_mocked_versions(dagster_library_versions: Mapping[str, str]):
    code_location = mock.MagicMock(spec=CodeLocation)
    code_location.get_dagster_library_versions = mock.MagicMock(
        return_value=dagster_library_versions
    )

    return CodeLocationEntry(
        origin=RegisteredCodeLocationOrigin("loaded_loc"),
        code_location=code_location,
        load_error=None,
        load_status=CodeLocationLoadStatus.LOADED,
        display_metadata={},
        update_timestamp=time.time(),
        version_key="test",
    )


def test_feature_flags(workspace_request_context):
    workspace_snapshot = workspace_request_context.get_code_location_entries()

    error_loc = workspace_snapshot["error_loc"]
    assert get_feature_flags_for_location(error_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }

    loading_loc = workspace_snapshot["loading_loc"]

    assert get_feature_flags_for_location(loading_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }

    # Old version that didn't even have it set
    really_old_version_loc = _location_with_mocked_versions({})

    assert get_feature_flags_for_location(really_old_version_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: True
    }

    # old pre 1.5.0 version
    pre_10_version_loc = _location_with_mocked_versions({"dagster": "0.15.5"})

    assert get_feature_flags_for_location(pre_10_version_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: True
    }

    # old pre 1.5.0 version
    old_version_loc = _location_with_mocked_versions({"dagster": "1.4.5"})

    assert get_feature_flags_for_location(old_version_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: True
    }

    # Post 1.5.0 version
    new_version_loc = _location_with_mocked_versions({"dagster": "1.5.0"})

    assert get_feature_flags_for_location(new_version_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }

    future_version_loc = _location_with_mocked_versions({"dagster": "2.5.0"})

    assert get_feature_flags_for_location(future_version_loc) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }

    gibberish_version = _location_with_mocked_versions({"dagster": "BLAHBLAHBLAH"})

    assert get_feature_flags_for_location(gibberish_version) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }

    dev_version = _location_with_mocked_versions({"dagster": "1!0+dev"})

    assert get_feature_flags_for_location(dev_version) == {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: False
    }
