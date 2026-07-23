import subprocess
import threading
import time
from collections.abc import Callable, Generator
from unittest.mock import MagicMock, create_autospec

import dagster as dg
import pytest
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.instance import DagsterInstance
from dagster._core.workspace.workspace import CodeLocationEntry
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.server import open_server_process
from dagster._grpc.server_watcher import create_grpc_watch_thread
from dagster._utils import find_free_port
from dagster._utils.error import SerializableErrorInfo
from dagster_shared.ipc import interrupt_ipc_subprocess_pid

LOCATION_NAME = "test_location"
TEST_WATCH_INTERVAL = 0.2


def wait_for_condition(
    fn: Callable[[], object], interval: int | float, timeout: int | float | None = None
) -> None:
    """Poll ``fn`` every ``interval`` seconds until it returns truthy or ``timeout`` elapses.

    Default timeout is ``min(5, interval * 60)`` — at most 5 seconds, but scaled down for
    very small intervals where 60 poll cycles is already plenty.
    """
    timeout = timeout if timeout is not None else min(5, interval * 60)
    start_time = time.time()
    while not fn():
        if time.time() - start_time > timeout:
            raise Exception(f"Timeout of {timeout} seconds exceeded for condition {fn}")

        time.sleep(interval)


@pytest.fixture
def unexpected_calls() -> Generator[list[str]]:
    """List of violations recorded by ``should_not_be_called`` callbacks; asserted empty on teardown."""
    list_of_unexpected_calls = []
    yield list_of_unexpected_calls
    assert not list_of_unexpected_calls, (
        f"Unexpected callback invocations: {list_of_unexpected_calls}"
    )


@pytest.fixture
def should_not_be_called(unexpected_calls: list[str]) -> Callable[[str], Callable[..., None]]:
    def _factory(name: str) -> Callable[..., None]:
        def _should_not_be_called(*args, **kwargs) -> None:
            unexpected_calls.append(f"{name}(args={args!r}, kwargs={kwargs!r})")

        return _should_not_be_called

    return _factory


@pytest.fixture
def create_server_process_and_watch_thread(
    get_location_entry: Callable[[str], CodeLocationEntry | None],
    called_event: dict[str, int],
    called_callback: dict[str, int],
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    should_not_be_called: Callable[[str], Callable[..., None]],
    instance: DagsterInstance,
    process_cleanup: list[subprocess.Popen],
) -> Callable[..., tuple[threading.Event, threading.Thread, subprocess.Popen]]:
    def _create_server_process_and_watch_thread(
        *,
        get_location_entry: Callable[[str], CodeLocationEntry | None] = get_location_entry,
        refresh_code_location: Callable[[str], None] = should_not_be_called(
            "refresh_code_location"
        ),
        on_disconnect: Callable[[str], None] = on_disconnect,
        on_reconnected: Callable[[str], None] = on_reconnected,
        on_updated: Callable[[str, str], None] = should_not_be_called("on_updated"),
        on_error: Callable[[str], None] = should_not_be_called("on_error"),
        watch_interval: float | None = None,
        max_reconnect_attempts: int | None = None,
        error_recovery_interval: float | None = TEST_WATCH_INTERVAL,
        fixed_server_id: str | None = None,
        port: int | None = None,
    ) -> tuple[threading.Event, threading.Thread, subprocess.Popen]:
        """Start a gRPC server subprocess and a watch thread against it.

        Defaults for ``on_updated``, ``on_error``, and ``refresh_code_location`` record a
        violation if invoked; pass explicit callbacks for events the test expects.

        ``error_recovery_interval`` defaults to a small value so the periodic recovery check (which
        is the only caller of ``get_location_entry``) runs frequently in tests.
        """
        port = port or find_free_port()

        server_process = open_server_process(
            instance.get_ref(),
            port=port,
            socket=None,
            server_command=GrpcServerCommand.API_GRPC,
            fixed_server_id=fixed_server_id,
        )
        process_cleanup.append(server_process)

        client = DagsterGrpcClient(port=port)

        event, watch_thread = create_grpc_watch_thread(
            LOCATION_NAME,
            client,
            get_location_entry=get_location_entry,
            refresh_code_location=refresh_code_location,
            on_disconnect=on_disconnect,
            on_reconnected=on_reconnected,
            on_updated=on_updated,
            on_error=on_error,
            watch_interval=watch_interval,
            max_reconnect_attempts=max_reconnect_attempts,
            error_recovery_interval=error_recovery_interval,
        )
        watch_thread.start()
        # Wait until the periodic recovery check has run twice, confirming the thread is alive and
        # looping. (get_location_entry is only called by the recovery check.)
        wait_for_condition(
            lambda: called_callback["get_location_entry_count"] >= 2,
            interval=watch_interval or TEST_WATCH_INTERVAL,
            timeout=5,
        )
        # Startup may produce at most one paired disconnect/reconnect cycle; reset counts so
        # each test starts from a clean baseline.
        assert called_event["on_reconnected_count"] == called_event["on_disconnect_count"] <= 1
        called_event["on_disconnect_count"] = 0
        called_event["on_reconnected_count"] = 0
        return event, watch_thread, server_process

    return _create_server_process_and_watch_thread


def test_run_grpc_watch_thread(
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    shutdown_event, watch_thread, _ = create_server_process_and_watch_thread()

    shutdown_event.set()
    watch_thread.join()


@pytest.fixture
def process_cleanup() -> Generator[list[subprocess.Popen]]:
    to_clean = []

    yield to_clean

    for process in to_clean:
        process.terminate()

    for process in to_clean:
        process.wait()


@pytest.fixture
def instance() -> Generator[DagsterInstance]:
    with dg.instance_for_test() as instance:
        yield instance


@pytest.fixture
def code_location_entry() -> CodeLocationEntry:
    return create_autospec(CodeLocationEntry, spec_set=True, instance=True)


@pytest.fixture
def called_event() -> dict[str, int]:
    return {
        "on_disconnect_count": 0,
        "on_reconnected_count": 0,
        "on_updated_count": 0,
        "on_error_count": 0,
    }


@pytest.fixture
def on_error(called_event: dict[str, int]) -> Callable[[str], None]:
    def _on_error(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_error_count"] += 1

    return _on_error


@pytest.fixture
def on_updated(called_event: dict[str, int]) -> Callable[[str, str], None]:
    def _on_updated(location_name: str, new_server_id: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_updated_count"] += 1

    return _on_updated


@pytest.fixture
def on_disconnect(called_event: dict[str, int]) -> Callable[[str], None]:
    def _on_disconnect(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_disconnect_count"] += 1

    return _on_disconnect


@pytest.fixture
def on_reconnected(called_event: dict[str, int]) -> Callable[[str], None]:
    def _on_reconnected(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_reconnected_count"] += 1

    return _on_reconnected


@pytest.fixture
def called_callback() -> dict[str, int]:
    return {
        "get_location_entry_count": 0,
        "refresh_code_location_count": 0,
    }


@pytest.fixture
def get_location_entry(
    called_callback: dict[str, int], code_location_entry: CodeLocationEntry
) -> Callable[[str], CodeLocationEntry | None]:
    def _get_location_entry(location_name: str) -> CodeLocationEntry | None:
        assert location_name == LOCATION_NAME
        called_callback["get_location_entry_count"] += 1
        return code_location_entry

    return _get_location_entry


@pytest.fixture
def refresh_code_location(called_callback: dict[str, int]) -> Callable[[str], None]:
    def _refresh_code_location(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_callback["refresh_code_location_count"] += 1

    return _refresh_code_location


def test_grpc_watch_thread_server_update(
    instance: DagsterInstance,
    process_cleanup: list[subprocess.Popen],
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    port = find_free_port()
    watch_interval = 0.2

    called = {}

    def on_updated(location_name: str, _) -> None:
        assert location_name == LOCATION_NAME
        called["yup"] = True

    # Start watch thread
    shutdown_event, watch_thread, server_process = create_server_process_and_watch_thread(
        on_updated=on_updated,
        watch_interval=watch_interval,
        port=port,
    )
    time.sleep(watch_interval * 3)
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


def test_grpc_watch_thread_server_reconnect(
    process_cleanup: list[subprocess.Popen],
    instance: DagsterInstance,
    called_event: dict[str, int],
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    port = find_free_port()
    fixed_server_id = "fixed_id"

    # Create initial server and start watch thread
    watch_interval = 0.2
    shutdown_event, watch_thread, server_process = create_server_process_and_watch_thread(
        watch_interval=watch_interval,
        port=port,
        fixed_server_id=fixed_server_id,
    )
    time.sleep(watch_interval * 3)

    # Wait three seconds, simulate restart server, wait three seconds
    interrupt_ipc_subprocess_pid(server_process.pid)
    wait_for_condition(lambda: called_event.get("on_disconnect_count"), watch_interval)

    server_process = open_server_process(
        instance.get_ref(),
        port=port,
        socket=None,
        fixed_server_id=fixed_server_id,
        server_command=GrpcServerCommand.API_GRPC,
    )
    process_cleanup.append(server_process)
    wait_for_condition(lambda: called_event.get("on_reconnected_count"), watch_interval)

    shutdown_event.set()
    watch_thread.join()


def test_grpc_watch_thread_server_error(
    process_cleanup: list[subprocess.Popen],
    instance: DagsterInstance,
    called_event: dict[str, int],
    on_error: Callable[[str], None],
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    port = find_free_port()
    fixed_server_id = "fixed_id"

    called = {}

    def on_updated(location_name: str, new_server_id: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_updated_count"] += 1
        called["on_updated"] = new_server_id

    # Create initial server and start watch thread
    watch_interval = 0.2
    max_reconnect_attempts = 3
    shutdown_event, watch_thread, server_process = create_server_process_and_watch_thread(
        on_updated=on_updated,
        on_error=on_error,
        watch_interval=watch_interval,
        max_reconnect_attempts=max_reconnect_attempts,
        port=port,
        fixed_server_id=fixed_server_id,
    )
    time.sleep(watch_interval * 3)

    # Simulate restart failure
    # Wait for reconnect attempts to exhaust and on_error callback to be called
    interrupt_ipc_subprocess_pid(server_process.pid)
    wait_for_condition(lambda: called_event.get("on_error_count"), watch_interval)

    assert called_event["on_disconnect_count"]
    assert called_event["on_error_count"]
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


def test_run_grpc_watch_without_server(
    called_event: dict[str, int],
    on_error: Callable[[str], None],
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    # Starting a thread for a server that never existed should immediately error out

    watch_interval = 0.2
    max_reconnect_attempts = 1

    shutdown_event, watch_thread, server_process = create_server_process_and_watch_thread(
        on_error=on_error,
        watch_interval=watch_interval,
        max_reconnect_attempts=max_reconnect_attempts,
    )
    interrupt_ipc_subprocess_pid(server_process.pid)

    time.sleep(watch_interval * 3)

    # Wait for reconnect attempts to exhaust and on_error callback to be called
    wait_for_condition(lambda: called_event.get("on_error_count"), watch_interval)

    shutdown_event.set()
    watch_thread.join()

    assert called_event["on_disconnect_count"]


def test_grpc_watch_thread_recovery_when_errored(
    code_location_entry: MagicMock,
    called_event: dict[str, int],
    called_callback: dict[str, int],
    refresh_code_location: Callable[[str], None],
    create_server_process_and_watch_thread: Callable[
        ..., tuple[threading.Event, threading.Thread, subprocess.Popen]
    ],
) -> None:
    """Verify the periodic recovery check refreshes a location stuck in a transient
    unreachable-error state, independently of the server-id watch/reconnect logic.

    Simulates a K8s rolling-deployment race: a prior workspace refresh failed (e.g. routed to a
    dying pod) leaving the entry errored, but the gRPC server is reachable. The recovery check
    must call ``refresh_code_location`` to recover, without firing any on_* event (recovery is
    fully decoupled from the gRPC reconnect loop).
    """
    no_events = {
        "on_disconnect_count": 0,
        "on_reconnected_count": 0,
        "on_updated_count": 0,
        "on_error_count": 0,
    }

    watch_interval = 0.1
    error_recovery_interval = 0.1
    shutdown_event, watch_thread, _ = create_server_process_and_watch_thread(
        refresh_code_location=refresh_code_location,
        watch_interval=watch_interval,
        error_recovery_interval=error_recovery_interval,
        fixed_server_id="fixed_id",
    )

    # Healthy entry: the recovery check runs but never refreshes.
    wait_for_condition(
        lambda: called_callback["get_location_entry_count"] >= 2,
        interval=watch_interval,
        timeout=5,
    )
    assert called_callback["refresh_code_location_count"] == 0
    assert called_event == no_events

    # Simulate the workspace entry stuck in an unreachable-error state.
    code_location_entry.load_error = SerializableErrorInfo(
        "Simulated failure", [], DagsterUserCodeUnreachableError.__name__
    )

    # The recovery check should detect the error and keep refreshing while it stays errored,
    # without the server ID having changed.
    wait_for_condition(
        lambda: called_callback["refresh_code_location_count"] >= 2,
        interval=watch_interval,
        timeout=5,
    )
    # Recovery is fully decoupled from the gRPC loop: no events fire.
    assert called_event == no_events

    # Clear the error — refresh attempts should stop.
    code_location_entry.load_error = None
    time.sleep(error_recovery_interval * 3)
    refresh_snapshot = called_callback["refresh_code_location_count"]
    time.sleep(error_recovery_interval * 5)
    assert called_callback["refresh_code_location_count"] == refresh_snapshot
    assert called_event == no_events

    shutdown_event.set()
    watch_thread.join()
