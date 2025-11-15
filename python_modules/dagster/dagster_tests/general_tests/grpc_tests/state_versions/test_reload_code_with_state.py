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
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_tests.general_tests.grpc_tests.test_persistent import entrypoints


def setup_test_components(project_dir):
    """Set up the test environment with component definitions."""
    # Create singleton component
    singleton_dir = project_dir / "src/foo_bar/defs/singleton_component"
    singleton_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        Path(__file__).parent / "singleton_component.py",
        singleton_dir / "local.py",
    )
    with (singleton_dir / "defs.yaml").open("w") as f:
        yaml.dump(
            {"type": ".local.SingletonComponent"},
            f,
        )

    # Create duplicitous component
    duplicitous_dir = project_dir / "src/foo_bar/defs/duplicitous_component"
    duplicitous_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        Path(__file__).parent / "duplicitous_component.py",
        duplicitous_dir / "local.py",
    )
    with (duplicitous_dir / "defs.yaml").open("w") as f:
        yaml.dump(
            {"type": ".local.DuplicitousComponent"},
            f,
        )


def get_asset_keys_from_server(client):
    """Get the set of asset keys currently available on the server."""
    list_repositories_response = sync_list_repositories_grpc(client)
    repo_symbol = list_repositories_response.repository_symbols[0]
    repo_name = repo_symbol.repository_name
    code_location_origin = GrpcServerCodeLocationOrigin(port=client.port, host=client.host)

    remote_repo_origin = RemoteRepositoryOrigin(
        code_location_origin=code_location_origin, repository_name=repo_name
    )

    serialized_repo = client.external_repository(
        remote_repo_origin,
        defer_snapshots=False,
    )
    repo_snap = dg.deserialize_value(serialized_repo, RepositorySnap)
    return {node.asset_key for node in repo_snap.asset_nodes}


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_reload_code_with_state_partial_reload(entrypoint):
    """Test selective partial reloading of components using reload_code_with_state."""
    port = find_free_port()

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        # Set up test components
        setup_test_components(project_dir)

        state_storage = instance.defs_state_storage
        assert state_storage is not None

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "state.txt"
            temp_path.touch()
            # the actual state is not important for the test
            state_storage.upload_state_from_path(
                key="SingletonComponent", version="v1", path=temp_path
            )
            state_storage.upload_state_from_path(
                key="DuplicitousComponent", version="v1", path=temp_path
            )

        # Create initial defs_state_info
        initial_state_info = state_storage.get_latest_defs_state_info()
        assert initial_state_info is not None
        assert initial_state_info.get_version("SingletonComponent") == "v1"
        assert initial_state_info.get_version("DuplicitousComponent") == "v1"

        # Start GRPC server
        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            str(project_dir / "src/foo_bar/definitions.py"),
            "--instance-ref",
            serialize_value(instance.get_ref()),
            "--defs-state-info",
            serialize_value(initial_state_info),
        ]

        process = subprocess.Popen(subprocess_args)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, subprocess_args)

            # Get initial asset keys - should have singleton and dup_0
            initial_assets = get_asset_keys_from_server(client)
            assert dg.AssetKey("singleton") in initial_assets
            assert dg.AssetKey("dup_0") in initial_assets
            assert len(initial_assets) == 2

            # Now update the state for DuplicitousComponent
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "state.txt"
                temp_path.touch()
                state_storage.upload_state_from_path(
                    key="DuplicitousComponent", version="v2", path=temp_path
                )

            # Test first partial reload - should increment duplicitous component to dup_1
            updated_state_info_1 = state_storage.get_latest_defs_state_info()
            assert updated_state_info_1 is not None
            assert updated_state_info_1.get_version("SingletonComponent") == "v1"
            assert updated_state_info_1.get_version("DuplicitousComponent") == "v2"

            serialized_state_info_1 = serialize_value(updated_state_info_1)
            reply_1 = client.reload_code_with_state(serialized_state_info_1, timeout=10)
            assert reply_1.serialized_error == "" or reply_1.serialized_error is None

            # Check assets after first reload - should have singleton and dup_1
            assets_after_reload_1 = get_asset_keys_from_server(client)
            assert dg.AssetKey("singleton") in assets_after_reload_1
            assert dg.AssetKey("dup_1") in assets_after_reload_1  # incremented!
            assert dg.AssetKey("dup_0") not in assets_after_reload_1  # old one gone
            assert len(assets_after_reload_1) == 2

            # Same as above
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "state.txt"
                temp_path.touch()
                state_storage.upload_state_from_path(
                    key="DuplicitousComponent", version="v3", path=temp_path
                )

            updated_state_info_2 = state_storage.get_latest_defs_state_info()
            assert updated_state_info_2 is not None
            assert updated_state_info_2.get_version("SingletonComponent") == "v1"
            assert updated_state_info_2.get_version("DuplicitousComponent") == "v3"

            serialized_state_info_2 = serialize_value(updated_state_info_2)
            reply_2 = client.reload_code_with_state(serialized_state_info_2, timeout=10)
            assert reply_2.serialized_error == "" or reply_2.serialized_error is None

            # Check assets after second reload - should have singleton and dup_2
            assets_after_reload_2 = get_asset_keys_from_server(client)
            assert dg.AssetKey("singleton") in assets_after_reload_2
            assert dg.AssetKey("dup_2") in assets_after_reload_2  # incremented again!
            assert dg.AssetKey("dup_1") not in assets_after_reload_2  # previous one gone
            assert len(assets_after_reload_2) == 2

            # Finally, we update the state for SingletonComponent, which should trigger an error
            # as it can only be loaded once
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "state.txt"
                temp_path.touch()
                state_storage.upload_state_from_path(
                    key="SingletonComponent", version="v2", path=temp_path
                )

            updated_state_info_3 = state_storage.get_latest_defs_state_info()
            assert updated_state_info_3 is not None
            assert updated_state_info_3.get_version("SingletonComponent") == "v2"
            assert updated_state_info_3.get_version("DuplicitousComponent") == "v3"

            serialized_state_info_3 = serialize_value(updated_state_info_3)
            reply_3 = client.reload_code_with_state(serialized_state_info_3, timeout=10)

            # This should result in an error because SingletonComponent can't be reloaded
            assert reply_3.serialized_error is not None and reply_3.serialized_error != ""

        finally:
            process.terminate()
            process.wait()
