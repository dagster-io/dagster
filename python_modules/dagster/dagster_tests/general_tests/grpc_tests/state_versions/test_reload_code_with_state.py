import shutil
import subprocess
import tempfile
from pathlib import Path

import dagster as dg
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
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_tests.general_tests.grpc_tests.test_persistent import entrypoints


def setup_test_components(project_dir):
    """Set up the test environment with both sample and duplicitous components."""
    # Create sample state-backed component (produces asset named after state content)
    sample_dir = project_dir / "src/foo_bar/defs/the_component"
    sample_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        Path(__file__).parent / "sample_state_backed_component.py",
        sample_dir / "local.py",
    )
    with (sample_dir / "defs.yaml").open("w") as f:
        yaml.dump({"type": ".local.SampleStateBackedComponent"}, f)

    # Create duplicitous component (tracks load count via sentinel files)
    dup_dir = project_dir / "src/foo_bar/defs/duplicitous_component"
    dup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        Path(__file__).parent / "duplicitous_component.py",
        dup_dir / "local.py",
    )
    with (dup_dir / "defs.yaml").open("w") as f:
        yaml.dump({"type": ".local.DuplicitousComponent"}, f)


def upload_state(defs_state_storage, key, version, content="placeholder"):
    """Upload state to the state storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        p = Path(temp_dir) / "state.json"
        p.write_text(content)
        defs_state_storage.upload_state_from_path(path=p, key=key, version=version)


def get_asset_keys_from_server(client):
    """Get the set of asset keys currently available on the server."""
    list_repositories_response = sync_list_repositories_grpc(client)
    repo_symbol = list_repositories_response.repository_symbols[0]
    repo_name = repo_symbol.repository_name
    code_location_origin = GrpcServerCodeLocationOrigin(port=client.port, host=client.host)

    remote_repo_origin = RemoteRepositoryOrigin(
        code_location_origin=code_location_origin, repository_name=repo_name
    )

    serialized_repo = client.external_repository(remote_repo_origin, defer_snapshots=False)
    repo_snap = dg.deserialize_value(serialized_repo, RepositorySnap)
    return {node.asset_key for node in repo_snap.asset_nodes}


def find_dup_index(asset_keys):
    """Find the current dup_N index from the asset keys.

    DuplicitousComponent produces assets named dup_0, dup_1, etc.
    Returns the integer N from the current dup_N asset.
    """
    for key in asset_keys:
        parts = key.path
        if len(parts) == 1 and parts[0].startswith("dup_"):
            return int(parts[0].split("_")[1])
    raise AssertionError(f"No dup_N asset found in {asset_keys}")


@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Timing issue with subprocesses having open files in temp dir while its being cleaned up.",
)
@pytest.mark.parametrize("entrypoint", entrypoints())
def test_reload_code_with_state_incremental(entrypoint):
    """Test that ReloadCodeWithState performs incremental reload.

    Uses two components:
    - SampleStateBackedComponent: produces an asset named after the state file content
    - DuplicitousComponent: tracks load count, producing dup_0, dup_1, etc.

    When we reload with only DuplicitousComponent's state changed, only that
    component should rebuild (dup_0 -> dup_1), while SampleStateBackedComponent
    stays untouched.
    """
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        setup_test_components(project_dir)

        defs_state_storage = instance.defs_state_storage
        assert defs_state_storage

        # Upload initial state for both components
        upload_state(defs_state_storage, "SampleStateBackedComponent", "v1", content="hi")
        upload_state(defs_state_storage, "DuplicitousComponent", "v1")

        initial_state_info = defs_state_storage.get_latest_defs_state_info()
        assert initial_state_info is not None

        # Start gRPC server with initial state
        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            str(project_dir / "src/foo_bar/definitions.py"),
            "--location-name",
            "foo-bar",
            "--instance-ref",
            serialize_value(instance.get_ref()),
            "--defs-state-info",
            serialize_value(initial_state_info),
        ]

        process = subprocess.Popen(subprocess_args)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, subprocess_args)

            # Verify initial state: should have "hi" asset and a dup_N asset
            initial_assets = get_asset_keys_from_server(client)
            assert dg.AssetKey("hi") in initial_assets
            n = find_dup_index(initial_assets)
            assert len(initial_assets) == 2

            initial_server_id = client.get_server_id()

            # Upload new state for DuplicitousComponent only
            upload_state(defs_state_storage, "DuplicitousComponent", "v2")

            updated_state_info = defs_state_storage.get_latest_defs_state_info()
            assert updated_state_info is not None
            assert updated_state_info.get_version("SampleStateBackedComponent") == "v1"
            assert updated_state_info.get_version("DuplicitousComponent") == "v2"

            # Reload with updated state
            reply = client.reload_code_with_state(serialize_value(updated_state_info), timeout=30)
            assert reply.serialized_error == "" or reply.serialized_error is None

            # Server ID should have changed
            new_server_id = client.get_server_id()
            assert new_server_id != initial_server_id
            assert reply.serialized_server_id == new_server_id

            # DuplicitousComponent should have rebuilt (dup_N -> dup_{N+1})
            # SampleStateBackedComponent should be unchanged (still "hi")
            assets_after_reload = get_asset_keys_from_server(client)
            assert dg.AssetKey("hi") in assets_after_reload
            assert dg.AssetKey(f"dup_{n + 1}") in assets_after_reload
            assert dg.AssetKey(f"dup_{n}") not in assets_after_reload
            assert len(assets_after_reload) == 2

            # Second reload with another DuplicitousComponent version change
            upload_state(defs_state_storage, "DuplicitousComponent", "v3")

            updated_state_info_2 = defs_state_storage.get_latest_defs_state_info()
            reply_2 = client.reload_code_with_state(
                serialize_value(updated_state_info_2), timeout=30
            )
            assert reply_2.serialized_error == "" or reply_2.serialized_error is None

            assets_after_reload_2 = get_asset_keys_from_server(client)
            assert dg.AssetKey("hi") in assets_after_reload_2
            assert dg.AssetKey(f"dup_{n + 2}") in assets_after_reload_2
            assert dg.AssetKey(f"dup_{n + 1}") not in assets_after_reload_2
            assert len(assets_after_reload_2) == 2

        finally:
            process.terminate()
            process.wait()


@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Timing issue with subprocesses having open files in temp dir while its being cleaned up.",
)
@pytest.mark.parametrize("entrypoint", entrypoints())
def test_reload_code_with_state_no_changes(entrypoint):
    """Test that reloading with the same state info is a no-op for components."""
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        setup_test_components(project_dir)

        defs_state_storage = instance.defs_state_storage
        assert defs_state_storage

        upload_state(defs_state_storage, "SampleStateBackedComponent", "v1", content="hi")
        upload_state(defs_state_storage, "DuplicitousComponent", "v1")

        initial_state_info = defs_state_storage.get_latest_defs_state_info()
        assert initial_state_info is not None

        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            str(project_dir / "src/foo_bar/definitions.py"),
            "--location-name",
            "foo-bar",
            "--instance-ref",
            serialize_value(instance.get_ref()),
            "--defs-state-info",
            serialize_value(initial_state_info),
        ]

        process = subprocess.Popen(subprocess_args)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, subprocess_args)

            initial_assets = get_asset_keys_from_server(client)
            n = find_dup_index(initial_assets)

            # Reload with the exact same state info (no version changes)
            reply = client.reload_code_with_state(serialize_value(initial_state_info), timeout=30)
            assert reply.serialized_error == "" or reply.serialized_error is None

            # DuplicitousComponent should NOT have been reloaded (still dup_N)
            assets_after_reload = get_asset_keys_from_server(client)
            assert dg.AssetKey(f"dup_{n}") in assets_after_reload
            assert dg.AssetKey(f"dup_{n + 1}") not in assets_after_reload

        finally:
            process.terminate()
            process.wait()
