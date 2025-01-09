import sys
import threading
import time
from unittest import mock

import pytest
from dagster import file_relative_path, job, repository
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.remote_representation.origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RegisteredCodeLocationOrigin,
)
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.server import GrpcServerProcess


@job
def noop_job():
    pass


@repository
def repo():
    return [noop_job]


@repository
def other_repo():
    return [noop_job]


def _can_connect(origin, endpoint, instance):
    try:
        with GrpcServerCodeLocation(
            origin=origin,
            server_id=endpoint.server_id,
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
    with instance_for_test() as instance:
        yield instance


def test_error_repo_in_registry(instance):
    error_origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="error_repo",
            python_file=file_relative_path(__file__, "error_repo.py"),
        ),
    )
    with GrpcServerRegistry(
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
                server_id=endpoint.server_id,
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
                server_id=endpoint.server_id,
                port=endpoint.port,
                socket=endpoint.socket,
                host=endpoint.host,
                watch_server=False,
                instance=instance,
            ):
                pass


def test_server_registry(instance):
    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with GrpcServerRegistry(
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


def test_registry_multithreading(instance):
    origin = ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with GrpcServerRegistry(
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


class TestMockProcessGrpcServerRegistry(GrpcServerRegistry):
    def __init__(self, instance):
        self.mocked_loadable_target_origin = None
        super().__init__(
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
        python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
    )

    second_loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="other_repo",
        python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
    )

    origin = RegisteredCodeLocationOrigin("test_location")

    with TestMockProcessGrpcServerRegistry(instance) as registry:
        registry.mocked_loadable_target_origin = first_loadable_target_origin

        endpoint_one = registry.get_grpc_endpoint(origin)
        assert registry.get_grpc_endpoint(origin).server_id == endpoint_one.server_id

        # Swap in a new LoadableTargetOrigin - the same origin new returns a different
        # endpoint
        registry.mocked_loadable_target_origin = second_loadable_target_origin

        endpoint_two = registry.get_grpc_endpoint(origin)

        assert endpoint_two.server_id != endpoint_one.server_id

    registry.wait_for_processes()
    assert not _can_connect(origin, endpoint_one, instance)
    assert not _can_connect(origin, endpoint_two, instance)


def test_failure_on_open_server_process(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="repo",
        python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
    )
    with mock.patch("dagster._grpc.server.open_server_process") as mock_open_server_process:
        mock_open_server_process.side_effect = Exception("OOPS")
        with pytest.raises(Exception, match="OOPS"):
            with GrpcServerProcess(
                instance_ref=instance.get_ref(),
                loadable_target_origin=loadable_target_origin,
            ):
                pass
