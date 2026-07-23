import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import dagster as dg
import dagster._check as check
import pytest
import yaml
from dagster._api.list_repositories import sync_list_repositories_grpc
from dagster._core.remote_origin import GrpcServerCodeLocationOrigin, RemoteRepositoryOrigin
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import wait_for_grpc_server
from dagster._serdes import serialize_value
from dagster._utils import find_free_port
from dagster_dg_core.utils import activate_venv
from dagster_shared import seven
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_tests.general_tests.grpc_tests.test_persistent import entrypoints


def get_asset_keys_from_server(client: DagsterGrpcClient) -> set:
    """Get the set of asset keys currently available on the server."""
    list_repositories_response = sync_list_repositories_grpc(client)
    repo_symbol = list_repositories_response.repository_symbols[0]
    repo_name = repo_symbol.repository_name
    host = check.not_none(client.host)
    code_location_origin = GrpcServerCodeLocationOrigin(port=client.port, host=host)

    remote_repo_origin = RemoteRepositoryOrigin(
        code_location_origin=code_location_origin, repository_name=repo_name
    )

    serialized_repo = client.external_repository(remote_repo_origin, defer_snapshots=False)
    repo_snap = dg.deserialize_value(serialized_repo, RepositorySnap)
    return {node.asset_key for node in repo_snap.asset_nodes}


if TYPE_CHECKING:
    from dagster._grpc.__generated__ import dagster_api_pb2


def setup_refreshable_component(project_dir: Path) -> None:
    comp_dir = project_dir / "src/foo_bar/defs/the_component"
    comp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        Path(__file__).parent / "refreshable_component.py",
        comp_dir / "local.py",
    )
    with (comp_dir / "defs.yaml").open("w") as f:
        yaml.dump({"type": ".local.RefreshableComponent"}, f)


def _start_server(
    entrypoint, project_dir: Path, instance, port: int, env: dict[str, str] | None = None
) -> subprocess.Popen:
    subprocess_args = entrypoint + [
        "--port",
        str(port),
        "--python-file",
        str(project_dir / "src/foo_bar/definitions.py"),
        "--location-name",
        "foo-bar",
        "--instance-ref",
        serialize_value(instance.get_ref()),
    ]
    subprocess_env = {**os.environ, **(env or {})}
    return subprocess.Popen(subprocess_args, env=subprocess_env)


@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Timing issue with subprocesses having open files in temp dir while its being cleaned up.",
)
@pytest.mark.parametrize("entrypoint", entrypoints())
def test_refresh_component_state(entrypoint):
    """Refresh writes new versioned state and returns a DefsStateInfo with that version."""
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        setup_refreshable_component(project_dir)

        defs_state_storage = instance.defs_state_storage
        assert defs_state_storage

        process = _start_server(entrypoint, project_dir, instance, port)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, [])

            # Initially the component has no state (build_defs returns empty Definitions).
            assert get_asset_keys_from_server(client) == set()

            reply = client.refresh_component_state(
                defs_state_keys=["RefreshableComponent"],
                timeout=30,
            )
            assert reply.serialized_error == ""
            assert reply.serialized_defs_state_info != ""

            info = dg.deserialize_value(reply.serialized_defs_state_info, DefsStateInfo)
            assert "RefreshableComponent" in info.info_mapping
            version_1 = info.get_version("RefreshableComponent")
            assert version_1 is not None

            # The new version is also visible in the underlying storage.
            stored = defs_state_storage.get_latest_defs_state_info()
            assert stored is not None
            assert stored.get_version("RefreshableComponent") == version_1

            # A second refresh produces a different version (write_state_to_path
            # generates fresh content each call).
            reply_2 = client.refresh_component_state(
                defs_state_keys=["RefreshableComponent"],
                timeout=30,
            )
            assert reply_2.serialized_error == ""
            info_2 = dg.deserialize_value(reply_2.serialized_defs_state_info, DefsStateInfo)
            version_2 = info_2.get_version("RefreshableComponent")
            assert version_2 is not None
            assert version_2 != version_1

        finally:
            process.terminate()
            process.wait()


@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Timing issue with subprocesses having open files in temp dir while its being cleaned up.",
)
@pytest.mark.parametrize("entrypoint", entrypoints())
def test_refresh_component_state_unknown_key(entrypoint):
    """Refreshing with an unknown key returns a structured error."""
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        setup_refreshable_component(project_dir)
        process = _start_server(entrypoint, project_dir, instance, port)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, [])

            reply = client.refresh_component_state(
                defs_state_keys=["does-not-exist"],
                timeout=30,
            )
            assert reply.serialized_error != ""
            assert "does-not-exist" in reply.serialized_error

        finally:
            process.terminate()
            process.wait()


@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Timing issue with subprocesses having open files in temp dir while its being cleaned up.",
)
@pytest.mark.parametrize("entrypoint", entrypoints())
def test_refresh_component_state_concurrent_same_key_serialized(entrypoint):
    """Two concurrent refresh requests for the same key serialize via the per-key lock."""
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        # Use a slow refreshable component (sleeps during write_state_to_path) so
        # we can observe whether the two requests overlap.
        comp_dir = project_dir / "src/foo_bar/defs/the_component"
        comp_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "slow_refreshable_component.py",
            comp_dir / "local.py",
        )
        with (comp_dir / "defs.yaml").open("w") as f:
            yaml.dump({"type": ".local.SlowRefreshableComponent"}, f)

        timestamps_file = project_dir / "slow_refresh_timestamps.txt"
        process = _start_server(
            entrypoint,
            project_dir,
            instance,
            port,
            env={"SLOW_REFRESH_TIMESTAMPS_FILE": str(timestamps_file)},
        )

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, [])

            replies: list[dagster_api_pb2.RefreshComponentStateReply] = []

            def _refresh() -> None:
                replies.append(
                    client.refresh_component_state(
                        defs_state_keys=["SlowRefreshableComponent"],
                        timeout=60,
                    )
                )

            t1 = threading.Thread(target=_refresh)
            t2 = threading.Thread(target=_refresh)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            assert len(replies) == 2
            for reply in replies:
                assert reply.serialized_error == ""

            # The slow component records its [start, end] timestamps to a file
            # at the path supplied via SLOW_REFRESH_TIMESTAMPS_FILE. With per-key
            # serialization, the two intervals must not overlap.
            assert timestamps_file.exists()
            intervals: list[tuple[float, float]] = []
            for line in timestamps_file.read_text().splitlines():
                if not line.strip():
                    continue
                start_str, end_str = line.split(",")
                intervals.append((float(start_str), float(end_str)))
            assert len(intervals) == 2
            intervals.sort()
            # The second invocation's start must be after the first's end.
            assert intervals[1][0] >= intervals[0][1], f"Refresh intervals overlapped: {intervals}"

        finally:
            process.terminate()
            process.wait()
