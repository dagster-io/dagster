import time

import pytest
from dagster._core.test_utils import instance_for_test
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import GrpcServerCommand, open_server_process
from dagster._grpc.server_watcher import create_grpc_watch_thread
from dagster._serdes.ipc import interrupt_ipc_subprocess_pid
from dagster._utils import find_free_port


def wait_for_condition(fn, interval, timeout=60):
    start_time = time.time()
    while not fn():
        if time.time() - start_time > timeout:
            raise Exception(f"Timeout of {timeout} seconds exceeded for condition {fn}")

        time.sleep(interval)


def test_run_grpc_watch_thread():
    client = DagsterGrpcClient(port=8080)
    shutdown_event, watch_thread = create_grpc_watch_thread("test_location", client)

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
    with instance_for_test() as instance:
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
        shutdown_event, watch_thread = create_grpc_watch_thread(
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
    shutdown_event, watch_thread = create_grpc_watch_thread(
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
    shutdown_event, watch_thread = create_grpc_watch_thread(
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

    shutdown_event, watch_thread = create_grpc_watch_thread(
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
