import os
import sys
import threading
import time
from unittest import mock

import dagster as dg
import pytest
from dagster._cli.dev import ProxyServerManager
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RegisteredCodeLocationOrigin,
)
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.server import GrpcServerProcess
from dagster._utils import get_terminate_signal
from dagster._utils.env import environ


@dg.job
def noop_job():
    pass


@dg.repository
def repo():
    return [noop_job]


@dg.repository
def other_repo():
    return [noop_job]


def _can_connect(origin, endpoint, instance):
    try:
        with GrpcServerCodeLocation(
            origin=origin,
            port=endpoint.port,
            socket=endpoint.socket,
            host=endpoint.host,
            watch_server=False,
            instance=instance,
        ):
            return True
    except Exception:
        return False


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


def test_error_repo_in_registry(instance):
    error_origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="error_repo",
            python_file=dg.file_relative_path(__file__, "error_repo.py"),
        ),
    )
    with GrpcServerRegistry(
        server_command=GrpcServerCommand.API_GRPC,
        instance_ref=instance.get_ref(),
        heartbeat_ttl=10,
        startup_timeout=5,
        wait_for_processes_on_shutdown=True,
    ) as registry:
        # Repository with a loading error does not raise an exception
        endpoint = registry.get_grpc_endpoint(error_origin)

        # But using that endpoint to load a location results in an error
        with pytest.raises(DagsterUserCodeProcessError, match="object is not callable"):
            with GrpcServerCodeLocation(
                origin=error_origin,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                watch_server=False,
                instance=instance,
            ):
                pass

        # that error is idempotent
        with pytest.raises(DagsterUserCodeProcessError, match="object is not callable"):
            with GrpcServerCodeLocation(
                origin=error_origin,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                watch_server=False,
                instance=instance,
            ):
                pass


def test_server_unexpectedly_killed(instance: DagsterInstance):
    target = PythonFileTarget(
        python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
        attribute="repo",
        working_directory=None,
        location_name=None,
    )
    with environ({"DAGSTER_CODE_SERVER_AUTO_RESTART_INTERVAL": "1"}):
        with ProxyServerManager(
            instance,
            workspace_load_target=target,
        ) as manager:
            origins = manager._origins  # noqa: SLF001
            assert len(origins) == 1
            origin = origins[0]
            registry = manager._grpc_server_registry  # noqa: SLF001
            endpoint_one = registry.get_grpc_endpoint(origin)  # type: ignore

            assert _can_connect(origin, endpoint_one, instance)

            # Kill the server process. A new server should be automatically started.
            process = registry._all_processes[0]  # noqa: SLF001
            pid = process.pid
            os.kill(pid, get_terminate_signal())
            time.sleep(5)
            endpoint_one = registry.get_grpc_endpoint(origin)  # type: ignore
            assert _can_connect(origin, endpoint_one, instance)


def test_reload_updates_server_id(instance: DagsterInstance):
    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with GrpcServerRegistry(
        server_command=GrpcServerCommand.CODE_SERVER_START,
        instance_ref=instance.get_ref(),
        heartbeat_ttl=10,
        startup_timeout=5,
        wait_for_processes_on_shutdown=True,
    ) as registry:
        endpoint_one = registry.get_grpc_endpoint(origin)

        assert _can_connect(origin, endpoint_one, instance)

        initial_server_id = endpoint_one.create_client().get_server_id()

        endpoint_one.create_client().reload_code(timeout=60)

        assert endpoint_one.create_client().get_server_id() != initial_server_id


@pytest.mark.parametrize(
    "server_command", [GrpcServerCommand.API_GRPC, GrpcServerCommand.CODE_SERVER_START]
)
def test_server_registry(instance, server_command: GrpcServerCommand):
    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with GrpcServerRegistry(
        server_command=server_command,
        instance_ref=instance.get_ref(),
        heartbeat_ttl=10,
        startup_timeout=5,
        wait_for_processes_on_shutdown=True,
    ) as registry:
        endpoint_one = registry.get_grpc_endpoint(origin)
        endpoint_two = registry.get_grpc_endpoint(origin)

        assert endpoint_two == endpoint_one

        assert _can_connect(origin, endpoint_one, instance)
        assert _can_connect(origin, endpoint_two, instance)

        endpoint_three = registry.reload_grpc_endpoint(origin)

        assert _can_connect(origin, endpoint_three, instance)

        start_time = time.time()
        while True:
            # Server at endpoint_one should eventually die due to heartbeat failure

            if not _can_connect(origin, endpoint_one, instance):
                break

            if time.time() - start_time > 30:
                raise Exception("Old Server never died after process manager released it")

            time.sleep(1)

    # Cleaned up once we have left the context
    assert not _can_connect(origin, endpoint_two, instance)
    assert not _can_connect(origin, endpoint_three, instance)


def _registry_thread(origin, registry, endpoint, event):
    if registry.get_grpc_endpoint(origin) == endpoint:
        event.set()


@pytest.mark.parametrize(
    "server_command", [GrpcServerCommand.API_GRPC, GrpcServerCommand.CODE_SERVER_START]
)
def test_registry_multithreading(instance, server_command: GrpcServerCommand):
    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with GrpcServerRegistry(
        server_command=server_command,
        instance_ref=instance.get_ref(),
        heartbeat_ttl=600,
        startup_timeout=30,
        wait_for_processes_on_shutdown=True,
    ) as registry:
        endpoint = registry.get_grpc_endpoint(origin)

        threads = []
        success_events = []
        for _index in range(5):
            event = threading.Event()
            thread = threading.Thread(
                target=_registry_thread, args=(origin, registry, endpoint, event)
            )
            threads.append(thread)
            success_events.append(event)
            thread.start()

        for thread in threads:
            thread.join()

        for event in success_events:
            assert event.is_set()

        assert _can_connect(origin, endpoint, instance)

    assert not _can_connect(origin, endpoint, instance)


class MockProcessGrpcServerRegistry(GrpcServerRegistry):
    def __init__(self, instance):
        self.mocked_loadable_target_origin = None
        super().__init__(
            server_command=GrpcServerCommand.API_GRPC,
            instance_ref=instance.get_ref(),
            heartbeat_ttl=600,
            startup_timeout=30,
            wait_for_processes_on_shutdown=True,
        )

    def supports_origin(self, code_location_origin):
        return isinstance(code_location_origin, RegisteredCodeLocationOrigin)

    def _get_loadable_target_origin(self, code_location_origin):
        return self.mocked_loadable_target_origin


def test_custom_loadable_target_origin(instance):
    # Verifies that you can swap out the LoadableTargetOrigin for the same
    # repository location origin
    first_loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="repo",
        python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
    )

    second_loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="other_repo",
        python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
    )

    origin = RegisteredCodeLocationOrigin("test_location")

    with MockProcessGrpcServerRegistry(instance) as registry:
        registry.mocked_loadable_target_origin = first_loadable_target_origin

        endpoint_one = registry.get_grpc_endpoint(origin)
        assert registry.get_grpc_endpoint(origin) == endpoint_one

        # Swap in a new LoadableTargetOrigin - the same origin new returns a different
        # endpoint
        registry.mocked_loadable_target_origin = second_loadable_target_origin

        endpoint_two = registry.get_grpc_endpoint(origin)

        assert endpoint_two != endpoint_one

    registry.wait_for_processes()
    assert not _can_connect(origin, endpoint_one, instance)
    assert not _can_connect(origin, endpoint_two, instance)


def test_failure_on_open_server_process(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="repo",
        python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
    )
    with mock.patch("dagster._grpc.server.open_server_process") as mock_open_server_process:
        mock_open_server_process.side_effect = Exception("OOPS")
        with pytest.raises(Exception, match="OOPS"):
            with GrpcServerProcess(
                server_command=GrpcServerCommand.API_GRPC,
                instance_ref=instance.get_ref(),
                loadable_target_origin=loadable_target_origin,
            ):
                pass


def test_open_server_process_sets_refresh_local_defs_state_env():
    """The reload-spawn flag is forwarded to the code server env — and only then
    (issue #34434).
    """
    from dagster._grpc.server import open_server_process

    with (
        mock.patch("dagster._grpc.server.open_ipc_subprocess") as mock_open_ipc_subprocess,
        mock.patch("dagster._grpc.server.wait_for_grpc_server"),
    ):
        mock_open_ipc_subprocess.return_value = mock.MagicMock()
        open_server_process(
            instance_ref=None,
            port=8888,
            socket=None,
            server_command=GrpcServerCommand.API_GRPC,
            loadable_target_origin=None,
        )
        env = mock_open_ipc_subprocess.call_args.kwargs["env"]
        assert "DAGSTER_REFRESH_LOCAL_DEFS_STATE_ON_LOAD" not in env

        open_server_process(
            instance_ref=None,
            port=8888,
            socket=None,
            server_command=GrpcServerCommand.API_GRPC,
            loadable_target_origin=None,
            refresh_local_defs_state_on_load=True,
        )
        env = mock_open_ipc_subprocess.call_args.kwargs["env"]
        assert env["DAGSTER_REFRESH_LOCAL_DEFS_STATE_ON_LOAD"] == "1"


def test_reload_grpc_endpoint_spawns_with_refresh_local_defs_state_flag():
    """Code servers spawned for a user-initiated reload carry the refresh flag;
    ordinary endpoint fetches do not (issue #34434).
    """
    captured: list = []

    class StubGrpcServerProcess:
        def __init__(self, **kwargs):
            captured.append(kwargs)
            self.port = 4321
            self.socket = None
            self.server_process = mock.MagicMock()

        def shutdown_server(self):
            pass

        def wait(self, timeout=30):
            pass

    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=dg.file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )
    with mock.patch("dagster._grpc.server.GrpcServerProcess", StubGrpcServerProcess):
        with GrpcServerRegistry(
            instance_ref=None,
            server_command=GrpcServerCommand.API_GRPC,
            heartbeat_ttl=10,
            startup_timeout=5,
            wait_for_processes_on_shutdown=False,
        ) as registry:
            registry.get_grpc_endpoint(origin)
            assert not captured[-1].get("refresh_local_defs_state_on_load")

            registry.reload_grpc_endpoint(origin)
            assert captured[-1].get("refresh_local_defs_state_on_load") is True
