import subprocess
import threading
import time
from collections import Counter
from collections.abc import Callable, Generator
from unittest.mock import create_autospec

import dagster as dg
import pytest
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.workspace.workspace import CodeLocationEntry
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.server import open_server_process
from dagster._grpc.server_watcher import MAX_RECONNECT_ATTEMPTS, create_grpc_watch_thread
from dagster._utils import find_free_port
from dagster._utils.error import SerializableErrorInfo
from dagster_shared.ipc import interrupt_ipc_subprocess_pid

LOCATION_NAME = "test_location"
TEST_WATCH_INTERVAL = 0.2


def wait_for_condition(
    fn: Callable[[], object], interval: int | float, timeout: int | float | None = None
) -> None:
    """Poll ``fn`` every ``interval`` seconds until it returns truthy or ``timeout`` elapses.

    If ``timeout`` is not provided, it defaults to ``min(5, interval * 60)``: capped at
    5 seconds for the long-interval case, but capped at ``interval * 60`` when ``interval``
    is small so we don't wait 5 full seconds when 60 poll cycles is already more than enough
    chances for the condition to become true.
    """
    timeout = timeout if timeout is not None else min(5, interval * 60)
    start_time = time.time()
    while not fn():
        if time.time() - start_time > timeout:
            raise Exception(f"Timeout of {timeout} seconds exceeded for condition {fn}")

        time.sleep(interval)


@pytest.fixture
def unexpected_calls() -> Generator[list[str]]:
    """Shared list used by ``should_not_be_called`` callbacks to record violations.

    Autouse teardown that fails the test if any ``should_not_be_called`` callback fired.
    """
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
    called_event: Counter[str],
    called_callback: Counter[str],
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    should_not_be_called: Callable[[str], Callable[..., None]],
    instance,
    process_cleanup,
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
        fixed_server_id: str | None = None,
        port: int | None = None,
    ) -> tuple[threading.Event, threading.Thread, subprocess.Popen]:
        """Test helper: creates a gRPC server + watch thread.

        on_error/on_updated callback defaults raise if unexpectedly invoked; pass explicit callbacks
        for events you expect.
        """
        port = port or find_free_port()

        # Create initial server
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
        )
        watch_thread.start()
        # Let the watch thread establish the server ID (at least 2 polls: one to discover the
        # server ID, one to confirm it is stable).
        wait_for_condition(
            lambda: called_callback["get_location_entry_count"] >= 2,
            interval=watch_interval or TEST_WATCH_INTERVAL,
            timeout=5,
        )
        # During startup the watch thread may briefly disconnect and reconnect (at most once),
        # but the two counts must match — we should never observe an unpaired disconnect.
        assert called_event["on_reconnected_count"] == called_event["on_disconnect_count"] <= 1
        # Reset counts so each test starts from a clean baseline regardless of any startup
        # disconnect/reconnect cycle observed above.
        called_event.update(
            {
                "on_disconnect_count": 0,
                "on_reconnected_count": 0,
                "on_updated_count": 0,
                "on_error_count": 0,
            }
        )
        return event, watch_thread, server_process

    return _create_server_process_and_watch_thread


def test_run_grpc_watch_thread(create_server_process_and_watch_thread):
    shutdown_event, watch_thread, _ = create_server_process_and_watch_thread()

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


@pytest.fixture
def code_location_entry() -> CodeLocationEntry:
    return create_autospec(CodeLocationEntry, spec_set=True, instance=True)


@pytest.fixture
def called_event() -> Counter[str]:
    return Counter(
        {
            "on_disconnect_count": 0,
            "on_reconnected_count": 0,
            "on_updated_count": 0,
            "on_error_count": 0,
        }
    )


@pytest.fixture
def on_error(called_event: Counter[str]) -> Callable[[str], None]:
    def _on_error(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_error_count"] += 1

    return _on_error


@pytest.fixture
def on_updated(called_event: Counter[str]) -> Callable[[str, str], None]:
    def _on_updated(location_name: str, new_server_id: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_updated_count"] += 1

    return _on_updated


@pytest.fixture
def on_disconnect(called_event: Counter[str]) -> Callable[[str], None]:
    def _on_disconnect(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_disconnect_count"] += 1

    return _on_disconnect


@pytest.fixture
def on_reconnected(called_event: Counter[str]) -> Callable[[str], None]:
    def _on_reconnected(location_name: str) -> None:
        assert location_name == LOCATION_NAME
        called_event["on_reconnected_count"] += 1

    return _on_reconnected


@pytest.fixture
def called_callback() -> Counter[str]:
    return Counter(
        {
            "get_location_entry_count": 0,
            "refresh_code_location_count": 0,
        }
    )


@pytest.fixture
def get_location_entry(
    called_callback: Counter[str], code_location_entry: CodeLocationEntry
) -> Callable[[str], CodeLocationEntry | None]:
    def _get_location_entry(location_name: str) -> CodeLocationEntry | None:
        assert location_name == LOCATION_NAME
        called_callback["get_location_entry_count"] += 1
        return code_location_entry

    return _get_location_entry


@pytest.fixture
def refresh_code_location(called_callback: Counter[str]) -> Callable[[str], None]:
    def _refresh_code_location(location_name) -> None:
        assert location_name == LOCATION_NAME
        called_callback["refresh_code_location_count"] += 1

    return _refresh_code_location


def test_grpc_watch_thread_server_update(
    instance, process_cleanup, create_server_process_and_watch_thread
):
    port = find_free_port()
    watch_interval = 0.2

    called = {}

    def on_updated(location_name, _):
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
    process_cleanup,
    instance,
    called_event,
    create_server_process_and_watch_thread,
):
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
    process_cleanup,
    instance,
    called_event,
    on_error,
    create_server_process_and_watch_thread,
):
    port = find_free_port()
    fixed_server_id = "fixed_id"

    called = {}

    def on_updated(location_name, new_server_id):
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
    called_event, on_error, create_server_process_and_watch_thread
):
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


@pytest.mark.parametrize("cycles_to_recover", [3, 20])
def test_grpc_watch_thread_recovery_when_errored(
    process_cleanup,
    instance,
    code_location_entry,
    called_event,
    called_callback,
    on_error,
    on_updated,
    refresh_code_location,
    create_server_process_and_watch_thread,
    cycles_to_recover,
):
    """Test that the watch thread fires on_disconnect + on_reconnected when the workspace entry
    is in an error state but the server is reachable.

    This simulates the K8s rolling deployment recovery scenario: the watch thread detected a new
    server ID and fired on_updated, but the workspace's refresh failed (e.g. gRPC call routed to
    dying pod). The watch thread should detect that the location is errored and fire disconnect +
    reconnect callbacks on the next poll cycle to trigger a recovery refresh.
    """
    fixed_server_id = "fixed_id"

    # Start watch thread with a short interval for faster test execution
    watch_interval = 0.1
    hooks = {}
    if cycles_to_recover > MAX_RECONNECT_ATTEMPTS:
        hooks["on_updated"] = on_updated
        hooks["on_error"] = on_error
    shutdown_event, watch_thread, _ = create_server_process_and_watch_thread(
        refresh_code_location=refresh_code_location,
        watch_interval=watch_interval,
        fixed_server_id=fixed_server_id,
        **hooks,
    )

    # Let the watch thread establish the server ID
    wait_for_condition(
        lambda: called_callback["get_location_entry_count"] >= 2,
        interval=watch_interval,
        timeout=5,
    )
    assert called_event == {
        "on_disconnect_count": 0,
        "on_reconnected_count": 0,
        "on_updated_count": 0,
        "on_error_count": 0,
    }
    assert called_callback["refresh_code_location_count"] == 0
    called_callback_snapshot = Counter(called_callback)

    # Simulate that the workspace entry is in an error state
    code_location_entry.load_error = SerializableErrorInfo(
        "Simulated failure", [], DagsterUserCodeUnreachableError.__name__
    )

    # The watch thread should detect the error and fire on_disconnect + on_reconnected even
    # though the server ID hasn't changed
    wait_for_condition(
        lambda: called_callback["refresh_code_location_count"] >= 1,
        interval=watch_interval,
        timeout=5,
    )
    assert (
        called_callback["get_location_entry_count"]
        > called_callback_snapshot["get_location_entry_count"]
    )
    called_event_expected = Counter(
        {
            "on_disconnect_count": 1,
            "on_reconnected_count": 0,
            "on_updated_count": 0,
            "on_error_count": 0,
        }
    )
    assert called_event == called_event_expected
    called_callback_snapshot = Counter(called_callback)
    time.sleep(watch_interval * cycles_to_recover)
    if cycles_to_recover > MAX_RECONNECT_ATTEMPTS:
        called_event_expected["on_error_count"] = 1
    assert called_event == called_event_expected

    # Clear the error — on_updated callback should fire. Sleep one interval to let any
    # in-flight poll cycle finish, then capture the count and verify it stays stable.
    code_location_entry.load_error = None
    called_event_expected[
        "on_reconnected_count" if cycles_to_recover < MAX_RECONNECT_ATTEMPTS else "on_updated_count"
    ] = 1
    wait_for_condition(
        lambda: called_event == called_event_expected,
        interval=watch_interval,
        timeout=5,
    )
    assert (
        called_callback["get_location_entry_count"]
        >= called_callback_snapshot["get_location_entry_count"] + cycles_to_recover
    )
    assert called_callback["refresh_code_location_count"] >= min(
        MAX_RECONNECT_ATTEMPTS - 1, cycles_to_recover
    )
    called_callback_snapshot = Counter(called_callback)
    # Wait for the watch thread to demonstrate it's still polling (>= 2 more get_location_entry
    # calls). Using wait_for_condition instead of a fixed sleep avoids a structural race where
    # the watch thread may already be mid-wait() when the test captures the snapshot — in 2x
    # watch_interval of fixed sleep only 1 full poll cycle reliably completes.
    wait_for_condition(
        lambda: (
            called_callback["get_location_entry_count"]
            >= called_callback_snapshot["get_location_entry_count"] + 2
        ),
        interval=watch_interval,
        timeout=watch_interval * 5,
    )
    # No additional events should have fired after recovery — the system should be settled.
    assert called_event == called_event_expected
    # No spurious refresh_code_location calls after recovery.
    assert (
        called_callback["refresh_code_location_count"]
        == called_callback_snapshot["refresh_code_location_count"]
    )

    shutdown_event.set()
    watch_thread.join()
