from unittest import mock

import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.remote_origin import GrpcServerCodeLocationOrigin
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import GrpcServerTarget


@pytest.mark.parametrize(
    "initial_server_id,initial_image,refreshed_server_id,refreshed_image,version_changes",
    [
        ("server-b", "image:a", "server-b", "image:b", True),
        ("server-a", "image:a", "server-b", "image:a", True),
        ("server-b", "image:b", "server-b", "image:b", False),
        ("server-b", None, "server-b", None, False),
        ("server-b", None, "server-b", "image:b", True),
        ("server-b", "image:b", "server-b", None, True),
    ],
    ids=[
        "image-corrected-with-same-server-id",
        "server-id-changed-with-same-image",
        "unchanged-image-and-server-id",
        "unchanged-missing-image",
        "image-added",
        "image-removed",
    ],
)
def test_grpc_location_version_key_on_refresh(
    initial_server_id: str,
    initial_image: str | None,
    refreshed_server_id: str,
    refreshed_image: str | None,
    version_changes: bool,
) -> None:
    locations = []
    for server_id, image in [
        (initial_server_id, initial_image),
        (refreshed_server_id, refreshed_image),
    ]:
        location = mock.MagicMock(spec=GrpcServerCodeLocation)
        location.server_id = server_id
        location.container_image = image
        location.get_display_metadata.return_value = {"image": image} if image is not None else {}
        locations.append(location)

    with (
        DagsterInstance.ephemeral() as instance,
        mock.patch.object(GrpcServerCodeLocationOrigin, "create_location", side_effect=locations),
        mock.patch.object(WorkspaceProcessContext, "_start_watch_thread"),
        mock.patch(
            "dagster._core.workspace.context.get_current_timestamp",
            side_effect=[1000.0, 2000.0],
        ),
        WorkspaceProcessContext(
            instance=instance,
            workspace_load_target=GrpcServerTarget(
                host="localhost", port=1234, socket=None, location_name="test_location"
            ),
            grpc_server_registry=mock.MagicMock(spec=GrpcServerRegistry),
        ) as context,
    ):
        initial_request = context.create_request_context()
        initial_entry = initial_request.get_code_location_entries()["test_location"]
        assert initial_entry.load_error is None
        assert (
            initial_request.get_code_location_statuses()[0].version_key == initial_entry.version_key
        )

        context.refresh_code_location("test_location")

        refreshed_request = context.create_request_context()
        refreshed_entry = refreshed_request.get_code_location_entries()["test_location"]
        assert refreshed_entry.load_error is None
        assert refreshed_entry.display_metadata.get("image") == refreshed_image
        assert refreshed_entry.update_timestamp != initial_entry.update_timestamp
        assert (
            refreshed_request.get_code_location_statuses()[0].version_key
            == refreshed_entry.version_key
        )
        assert (refreshed_entry.version_key != initial_entry.version_key) == version_changes
