import sys
import threading
import time

from dagster import file_relative_path, pipeline, repository
from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.core.host_representation.location_manager import RepositoryLocationManager
from dagster.core.host_representation.origin import ManagedGrpcPythonEnvRepositoryLocationOrigin
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin


@pipeline
def noop_pipeline():
    pass


@repository
def repo():
    return [noop_pipeline]


def _can_connect(origin, endpoint):
    try:
        with GrpcServerRepositoryLocation(
            origin=origin,
            server_id=endpoint.server_id,
            port=endpoint.port,
            socket=endpoint.socket,
            host=endpoint.host,
            watch_server=False,
        ):
            return True
    except Exception:  # pylint: disable=broad-except
        return False


def test_process_server_registry():

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with ProcessGrpcServerRegistry(
        wait_for_processes_on_exit=True, reload_interval=5, heartbeat_ttl=10
    ) as registry:

        with RepositoryLocationManager(registry) as location_manager:
            endpoint_one = registry.get_grpc_endpoint(origin)
            location_one = location_manager.get_location(origin)

            endpoint_two = registry.get_grpc_endpoint(origin)
            location_two = location_manager.get_location(origin)

            assert endpoint_two == endpoint_one
            assert location_two == location_one

            assert _can_connect(origin, endpoint_one)
            assert _can_connect(origin, endpoint_two)

            start_time = time.time()
            while True:

                # Registry should return a new server endpoint after 5 seconds
                endpoint_three = registry.get_grpc_endpoint(origin)

                if endpoint_three.server_id != endpoint_one.server_id:

                    # Location manager now produces a new location as well
                    location_three = location_manager.get_location(origin)
                    assert location_three != location_one

                    break

                if time.time() - start_time > 15:
                    raise Exception("Server ID never changed")

                time.sleep(1)

            assert _can_connect(origin, endpoint_three)
            # Leave location_manager context, all heartbeats stop

        start_time = time.time()
        while True:
            # Server at endpoint_one should eventually die due to heartbeat failure

            if not _can_connect(origin, endpoint_one):
                break

            if time.time() - start_time > 30:
                raise Exception("Old Server never died after process manager released it")

            time.sleep(1)

        # Make one more fresh process, then leave the context so that it will be cleaned up
        while True:
            endpoint_four = registry.get_grpc_endpoint(origin)

            if endpoint_four.server_id != endpoint_three.server_id:
                assert _can_connect(origin, endpoint_four)
                break

    # Once we leave the ProcessGrpcServerRegistry context, all processes should be cleaned up
    # (if wait_for_processes_on_exit was set)
    assert not _can_connect(origin, endpoint_three)
    assert not _can_connect(origin, endpoint_four)


def _registry_thread(origin, registry, endpoint, event):
    if registry.get_grpc_endpoint(origin) == endpoint:
        event.set()


def test_registry_multithreading():
    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="repo",
            python_file=file_relative_path(__file__, "test_grpc_server_registry.py"),
        ),
    )

    with ProcessGrpcServerRegistry(
        wait_for_processes_on_exit=True, reload_interval=300, heartbeat_ttl=600
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

        assert _can_connect(origin, endpoint)

    assert not _can_connect(origin, endpoint)
