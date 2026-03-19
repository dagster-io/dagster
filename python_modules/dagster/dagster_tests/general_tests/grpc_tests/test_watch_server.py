import threading
import time
from collections.abc import Callable

import dagster as dg
import pytest
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.server import open_server_process
from dagster._grpc.server_watcher import create_grpc_watch_thread
from dagster._utils import find_free_port
from dagster_shared.ipc import interrupt_ipc_subprocess_pid


def wait_for_condition(
    fn: Callable[[], object], interval: int | float, timeout: int | float = 60
) -> None:
    start_time = time.time()
    while not fn():
        if time.time() - start_time > timeout:
            raise Exception(f"Timeout of {timeout} seconds exceeded for condition {fn}")

        time.sleep(interval)


_noop: Callable = lambda *a: None
_no_recovery_needed: Callable[[str, str], bool] = lambda *a: False


def _create_watch_thread(
    location_name: str,
    client: DagsterGrpcClient,
    on_disconnect: Callable[[str], None] = _noop,
    on_reconnected: Callable[[str], None] = _noop,
    on_updated: Callable[[str, str], None] = _noop,
    on_error: Callable[[str], None] = _noop,
    needs_location_refresh: Callable[[str, str], bool] = _no_recovery_needed,
    **kwargs: object,
) -> tuple[threading.Event, threading.Thread]:
    """Test helper that provides noop defaults for all callbacks."""
    return create_grpc_watch_thread(
        location_name,
        client,
        on_disconnect=on_disconnect,
        on_reconnected=on_reconnected,
        on_updated=on_updated,
        on_error=on_error,
        needs_location_refresh=needs_location_refresh,
        **kwargs,
    )


def test_run_grpc_watch_thread():
    client = DagsterGrpcClient(port=8080)
    shutdown_event, watch_thread = _create_watch_thread("test_location", client)

    watch_thread.start()
    shutdown_event.set()
    watch_thread.join()


@pytest.fixture
def process_cleanup():
    to_clean = []

    yield to_clean

    for process in to_clean:
        process.terminate()

    for process in to_clean:
        process.wait()


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


def test_grpc_watch_thread_server_update(instance, process_cleanup):
    port = find_free_port()

    called = {}

    def on_updated(location_name, _):
        assert location_name == "test_location"
        called["yup"] = True

    # Create initial server
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    try:
        # Start watch thread
        client = DagsterGrpcClient(port=port)
        watch_interval = 1
        shutdown_event, watch_thread = _create_watch_thread(
            "test_location",
            client,
            on_updated=on_updated,
            watch_interval=watch_interval,
        )
        watch_thread.start()
        time.sleep(watch_interval * 3)
    finally:
        interrupt_ipc_subprocess_pid(server_process.pid)

    assert not called

    # Create updated server
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    try:
        wait_for_condition(lambda: called, interval=watch_interval)
    finally:
        interrupt_ipc_subprocess_pid(server_process.pid)

    shutdown_event.set()
    watch_thread.join()
    assert called


def test_grpc_watch_thread_server_reconnect(process_cleanup, instance):
    port = find_free_port()
    fixed_server_id = "fixed_id"

    called = {}

    def on_disconnect(location_name):
        assert location_name == "test_location"
        called["on_disconnect"] = True

    def on_reconnected(location_name):
        assert location_name == "test_location"
        called["on_reconnected"] = True

    def should_not_be_called(*args, **kwargs):
        raise Exception("This method should not be called")

    # Create initial server
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=fixed_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    # Start watch thread
    client = DagsterGrpcClient(port=port)
    watch_interval = 1
    shutdown_event, watch_thread = _create_watch_thread(
        "test_location",
        client,
        on_disconnect=on_disconnect,
        on_reconnected=on_reconnected,
        on_updated=should_not_be_called,
        on_error=should_not_be_called,
        watch_interval=watch_interval,
    )
    watch_thread.start()
    time.sleep(watch_interval * 3)

    # Wait three seconds, simulate restart server, wait three seconds
    interrupt_ipc_subprocess_pid(server_process.pid)
    wait_for_condition(lambda: called.get("on_disconnect"), watch_interval)

    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=fixed_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)
    wait_for_condition(lambda: called.get("on_reconnected"), watch_interval)

    shutdown_event.set()
    watch_thread.join()


def test_grpc_watch_thread_server_error(process_cleanup, instance):
    port = find_free_port()
    fixed_server_id = "fixed_id"

    called = {}

    def on_disconnect(location_name):
        assert location_name == "test_location"
        called["on_disconnect"] = True

    def on_error(location_name):
        assert location_name == "test_location"

        called["on_error"] = True

    def on_updated(location_name, new_server_id):
        assert location_name == "test_location"
        called["on_updated"] = new_server_id

    def should_not_be_called(*args, **kwargs):
        raise Exception("This method should not be called")

    # Create initial server
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=fixed_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    # Start watch thread
    client = DagsterGrpcClient(port=port)
    watch_interval = 1
    max_reconnect_attempts = 3
    shutdown_event, watch_thread = _create_watch_thread(
        "test_location",
        client,
        on_disconnect=on_disconnect,
        on_reconnected=should_not_be_called,
        on_updated=on_updated,
        on_error=on_error,
        watch_interval=watch_interval,
        max_reconnect_attempts=max_reconnect_attempts,
    )
    watch_thread.start()
    time.sleep(watch_interval * 3)

    # Simulate restart failure
    # Wait for reconnect attempts to exhaust and on_error callback to be called
    interrupt_ipc_subprocess_pid(server_process.pid)
    wait_for_condition(lambda: called.get("on_error"), watch_interval)

    assert called["on_disconnect"]
    assert called["on_error"]
    assert not called.get("on_updated")

    new_server_id = "new_server_id"
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=new_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    wait_for_condition(lambda: called.get("on_updated"), watch_interval)

    shutdown_event.set()
    watch_thread.join()

    assert called["on_updated"] == new_server_id


def test_run_grpc_watch_without_server():
    # Starting a thread for a server that never existed should immediately error out

    client = DagsterGrpcClient(port=8080)
    watch_interval = 1
    max_reconnect_attempts = 1

    called = {}

    def on_disconnect(location_name):
        assert location_name == "test_location"
        called["on_disconnect"] = True

    def on_error(location_name):
        assert location_name == "test_location"
        called["on_error"] = True

    def should_not_be_called(*args, **kwargs):
        raise Exception("This method should not be called")

    shutdown_event, watch_thread = _create_watch_thread(
        "test_location",
        client,
        on_disconnect=on_disconnect,
        on_reconnected=should_not_be_called,
        on_updated=should_not_be_called,
        on_error=on_error,
        watch_interval=watch_interval,
        max_reconnect_attempts=max_reconnect_attempts,
    )

    watch_thread.start()
    time.sleep(watch_interval * 3)

    # Wait for reconnect attempts to exhaust and on_error callback to be called
    wait_for_condition(lambda: called.get("on_error"), watch_interval)

    shutdown_event.set()
    watch_thread.join()

    assert called["on_disconnect"]


def test_grpc_watch_thread_recovery_when_errored(process_cleanup, instance):
    """Test that the watch thread fires on_disconnect + on_reconnected when the workspace entry
    is in an error state but the server is reachable.

    This simulates the K8s rolling deployment recovery scenario: the watch thread detected a new
    server ID and fired on_updated, but the workspace's refresh failed (e.g. gRPC call routed to
    dying pod). The watch thread should detect that the location is errored and fire disconnect +
    reconnect callbacks on the next poll cycle to trigger a recovery refresh.
    """
    port = find_free_port()
    fixed_server_id = "fixed_id"

    called = {
        "on_disconnect_count": 0,
        "on_reconnected_count": 0,
        "on_updated_count": 0,
        "on_error_count": 0,
        "simulate_error": False,
    }

    def on_disconnect(location_name):
        assert location_name == "test_location"
        called["on_disconnect_count"] += 1

    def on_reconnected(location_name):
        assert location_name == "test_location"
        called["on_reconnected_count"] += 1

    def on_updated(location_name, new_server_id):
        assert location_name == "test_location"
        called["on_updated_count"] += 1

    def on_error(location_name):
        assert location_name == "test_location"
        called["on_error_count"] += 1

    def has_error(location_name, version_key):
        return called["simulate_error"]

    # Create server
    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=fixed_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)

    # Start watch thread with a short interval for faster test execution
    client = DagsterGrpcClient(port=port)
    watch_interval = 0.1
    shutdown_event, watch_thread = _create_watch_thread(
        "test_location",
        client,
        on_disconnect=on_disconnect,
        on_reconnected=on_reconnected,
        on_updated=on_updated,
        on_error=on_error,
        needs_location_refresh=has_error,
        watch_interval=watch_interval,
    )
    watch_thread.start()

    # Let the watch thread establish the server ID
    time.sleep(watch_interval * 5)
    assert called["on_disconnect_count"] == 0
    assert called["on_reconnected_count"] == 0

    # Simulate that the workspace entry is in an error state
    called["simulate_error"] = True

    # The watch thread should detect the error and fire on_disconnect + on_reconnected even
    # though the server ID hasn't changed
    wait_for_condition(
        lambda: called["on_reconnected_count"] > 0,
        interval=watch_interval,
        timeout=watch_interval * 5,
    )
    assert called["on_disconnect_count"] > 0

    # Callbacks should keep firing on each poll cycle while the error persists
    reconnect_count_after_first = called["on_reconnected_count"]
    disconnect_count_after_first = called["on_disconnect_count"]
    wait_for_condition(
        lambda: called["on_reconnected_count"] > reconnect_count_after_first,
        interval=watch_interval,
        timeout=watch_interval * 5,
    )
    assert called["on_disconnect_count"] > disconnect_count_after_first

    # Clear the error — callbacks should stop firing. Sleep one interval to let any
    # in-flight poll cycle finish, then capture the count and verify it stays stable.
    called["simulate_error"] = False
    time.sleep(watch_interval)
    disconnect_count_after_clear = called["on_disconnect_count"]
    reconnect_count_after_clear = called["on_reconnected_count"]
    time.sleep(watch_interval * 2)
    assert called["on_disconnect_count"] == disconnect_count_after_clear
    assert called["on_reconnected_count"] == reconnect_count_after_clear
    # Once stable, disconnect and reconnect counts should be equal (they fire in pairs)
    assert called["on_disconnect_count"] == called["on_reconnected_count"]

    shutdown_event.set()
    watch_thread.join()
