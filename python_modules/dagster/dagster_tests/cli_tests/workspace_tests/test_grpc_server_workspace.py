import pytest
import yaml
from dagster import seven
from dagster.check import CheckError
from dagster.cli.workspace import Workspace
from dagster.cli.workspace.load import load_workspace_from_config
from dagster.core.host_representation.handle import UserProcessApi
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import file_relative_path


@pytest.mark.skipif(seven.IS_WINDOWS, reason="no named sockets on Windows")
def test_grpc_socket_workspace():

    with GrpcServerProcess().create_ephemeral_client() as first_server:
        with GrpcServerProcess().create_ephemeral_client() as second_server:
            first_socket = first_server.socket
            second_socket = second_server.socket
            workspace_yaml = """
load_from:
- grpc_server:
    host: localhost
    socket: {socket_one}
- grpc_server:
    socket: {socket_two}
    location_name: 'local_port_default_host'
                """.format(
                socket_one=first_socket, socket_two=second_socket
            )

            workspace = load_workspace_from_config(
                yaml.safe_load(workspace_yaml),
                # fake out as if it were loaded by a yaml file in this directory
                file_relative_path(__file__, "not_a_real.yaml"),
                python_user_process_api=UserProcessApi.CLI,  # doesn't affect grpc_server locations
            )
            assert isinstance(workspace, Workspace)
            assert len(workspace.repository_location_handles) == 2

            default_location_name = "grpc:localhost:{socket}".format(socket=first_socket)
            assert workspace.has_repository_location_handle(default_location_name)
            local_port = workspace.get_repository_location_handle(default_location_name)

            assert local_port.socket == first_socket
            assert local_port.host == "localhost"
            assert local_port.port is None

            assert workspace.has_repository_location_handle("local_port_default_host")
            local_port_default_host = workspace.get_repository_location_handle(
                "local_port_default_host"
            )

            assert local_port_default_host.socket == second_socket
            assert local_port_default_host.host == "localhost"
            assert local_port_default_host.port is None

            assert all(map(lambda x: x.location_name, workspace.repository_location_handles))


def test_grpc_server_workspace():
    with GrpcServerProcess(force_port=True).create_ephemeral_client() as first_server:
        with GrpcServerProcess(force_port=True).create_ephemeral_client() as second_server:
            first_port = first_server.port
            second_port = second_server.port
            workspace_yaml = """
load_from:
- grpc_server:
    host: localhost
    port: {port_one}
- grpc_server:
    port: {port_two}
    location_name: 'local_port_default_host'
                """.format(
                port_one=first_port, port_two=second_port
            )

            workspace = load_workspace_from_config(
                yaml.safe_load(workspace_yaml),
                # fake out as if it were loaded by a yaml file in this directory
                file_relative_path(__file__, "not_a_real.yaml"),
                UserProcessApi.CLI,
            )
            assert isinstance(workspace, Workspace)
            assert len(workspace.repository_location_handles) == 2

            default_location_name = "grpc:localhost:{port}".format(port=first_port)
            assert workspace.has_repository_location_handle(default_location_name)
            local_port = workspace.get_repository_location_handle(default_location_name)

            assert local_port.port == first_port
            assert local_port.host == "localhost"
            assert local_port.socket is None

            assert workspace.has_repository_location_handle("local_port_default_host")
            local_port_default_host = workspace.get_repository_location_handle(
                "local_port_default_host"
            )

            assert local_port_default_host.port == second_port
            assert local_port_default_host.host == "localhost"
            assert local_port_default_host.socket is None

            assert all(map(lambda x: x.location_name, workspace.repository_location_handles))


def test_cannot_set_socket_and_port():
    workspace_yaml = """
load_from:
  - grpc_server:
      socket: myname
      port: 5678

    """

    with pytest.raises(CheckError, match="must supply either a socket or a port"):
        load_workspace_from_config(
            yaml.safe_load(workspace_yaml),
            # fake out as if it were loaded by a yaml file in this directory
            file_relative_path(__file__, "not_a_real.yaml"),
            UserProcessApi.CLI,
        )
