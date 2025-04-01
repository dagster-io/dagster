from contextlib import ExitStack

import pytest
import yaml
from dagster._check import CheckError
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.remote_representation import GrpcServerCodeLocationOrigin
from dagster._core.test_utils import environ, instance_for_test
from dagster._core.workspace.load import location_origins_from_config
from dagster._grpc.server import GrpcServerProcess
from dagster._utils import file_relative_path
from dagster_shared import seven


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


@pytest.mark.skipif(seven.IS_WINDOWS, reason="no named sockets on Windows")
def test_grpc_socket_workspace(instance):
    with GrpcServerProcess(
        instance_ref=instance.get_ref(), wait_on_exit=True
    ) as first_server_process:
        first_server = first_server_process.create_client()
        with GrpcServerProcess(
            instance_ref=instance.get_ref(), wait_on_exit=True
        ) as second_server_process:
            second_server = second_server_process.create_client()
            first_socket = first_server.socket
            second_socket = second_server.socket
            workspace_yaml = f"""
load_from:
- grpc_server:
    host: localhost
    socket: {first_socket}
- grpc_server:
    socket: {second_socket}
    location_name: 'local_port_default_host'
                """

            origins = location_origins_from_config(
                yaml.safe_load(workspace_yaml),
                # fake out as if it were loaded by a yaml file in this directory
                file_relative_path(__file__, "not_a_real.yaml"),
            )

            with ExitStack() as stack:
                code_locations = {
                    name: stack.enter_context(origin.create_location(instance))
                    for name, origin in origins.items()
                }
                assert len(code_locations) == 2

                default_location_name = f"grpc:localhost:{first_socket}"
                assert code_locations.get(default_location_name)
                local_port = code_locations.get(default_location_name)

                assert local_port.socket == first_socket  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port.host == "localhost"  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port.port is None  # pyright: ignore[reportOptionalMemberAccess]

                assert code_locations.get("local_port_default_host")
                local_port_default_host = code_locations.get("local_port_default_host")

                assert local_port_default_host.socket == second_socket  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port_default_host.host == "localhost"  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port_default_host.port is None  # pyright: ignore[reportOptionalMemberAccess]

                assert all(map(lambda x: x.name, code_locations.values()))


def test_grpc_server_env_vars():
    with environ(
        {
            "FOO_PORT": "1234",
            "FOO_SOCKET": "barsocket",
            "FOO_HOST": "barhost",
        }
    ):
        valid_yaml = """
    load_from:
        - grpc_server:
            host:
              env: FOO_HOST
            port:
              env: FOO_PORT
            location_name: 'my_grpc_server_port'
        - grpc_server:
            host:
              env: FOO_HOST
            socket:
              env: FOO_SOCKET
            location_name: 'my_grpc_server_socket'
    """

        origins = location_origins_from_config(
            yaml.safe_load(valid_yaml),
            file_relative_path(__file__, "not_a_real.yaml"),
        )

        assert len(origins) == 2

        port_origin = origins["my_grpc_server_port"]
        assert isinstance(origins["my_grpc_server_port"], GrpcServerCodeLocationOrigin)

        assert port_origin.port == 1234  # pyright: ignore[reportAttributeAccessIssue]
        assert port_origin.host == "barhost"  # pyright: ignore[reportAttributeAccessIssue]

        socket_origin = origins["my_grpc_server_socket"]
        assert isinstance(origins["my_grpc_server_socket"], GrpcServerCodeLocationOrigin)

        assert socket_origin.socket == "barsocket"  # pyright: ignore[reportAttributeAccessIssue]
        assert socket_origin.host == "barhost"  # pyright: ignore[reportAttributeAccessIssue]


def test_ssl_grpc_server_workspace(instance):
    with GrpcServerProcess(
        instance_ref=instance.get_ref(), force_port=True, wait_on_exit=True
    ) as server_process:
        client = server_process.create_client()
        assert client.heartbeat(echo="Hello")

        port = server_process.port
        ssl_yaml = f"""
load_from:
- grpc_server:
    host: localhost
    port: {port}
    ssl: true
"""
        origins = location_origins_from_config(
            yaml.safe_load(ssl_yaml),
            # fake out as if it were loaded by a yaml file in this directory
            file_relative_path(__file__, "not_a_real.yaml"),
        )
        origin = next(iter(origins.values()))
        assert origin.use_ssl  # pyright: ignore[reportAttributeAccessIssue]

        # Actually connecting to the server will fail since it's expecting SSL
        # and we didn't set up the server with SSL
        try:
            with origin.create_location(instance):
                assert False
        except DagsterUserCodeUnreachableError:
            pass


def test_grpc_server_workspace(instance):
    with GrpcServerProcess(
        instance_ref=instance.get_ref(), force_port=True, wait_on_exit=True
    ) as first_server_process:
        first_server = first_server_process.create_client()
        with GrpcServerProcess(
            instance_ref=instance.get_ref(), force_port=True, wait_on_exit=True
        ) as second_server_process:
            second_server = second_server_process.create_client()
            first_port = first_server.port
            second_port = second_server.port
            workspace_yaml = f"""
load_from:
- grpc_server:
    host: localhost
    port: {first_port}
- grpc_server:
    port: {second_port}
    location_name: 'local_port_default_host'
                """

            origins = location_origins_from_config(
                yaml.safe_load(workspace_yaml),
                # fake out as if it were loaded by a yaml file in this directory
                file_relative_path(__file__, "not_a_real.yaml"),
            )

            with ExitStack() as stack:
                code_locations = {
                    name: stack.enter_context(origin.create_location(instance))
                    for name, origin in origins.items()
                }
                assert len(code_locations) == 2

                default_location_name = f"grpc:localhost:{first_port}"
                assert code_locations.get(default_location_name)
                local_port = code_locations.get(default_location_name)

                assert local_port.port == first_port  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port.host == "localhost"  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port.socket is None  # pyright: ignore[reportOptionalMemberAccess]

                assert code_locations.get("local_port_default_host")
                local_port_default_host = code_locations.get("local_port_default_host")

                assert local_port_default_host.port == second_port  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port_default_host.host == "localhost"  # pyright: ignore[reportOptionalMemberAccess]
                assert local_port_default_host.socket is None  # pyright: ignore[reportOptionalMemberAccess]

                assert all(map(lambda x: x.name, code_locations.values()))


def test_cannot_set_socket_and_port():
    workspace_yaml = """
load_from:
  - grpc_server:
      socket: myname
      port: 5678
    """

    with pytest.raises(CheckError, match="must supply either a socket or a port"):
        location_origins_from_config(
            yaml.safe_load(workspace_yaml),
            # fake out as if it were loaded by a yaml file in this directory
            file_relative_path(__file__, "not_a_real.yaml"),
        )
