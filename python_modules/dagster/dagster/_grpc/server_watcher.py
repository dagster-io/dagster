import threading
from collections.abc import Callable

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._grpc.client import DagsterGrpcClient

WATCH_INTERVAL = 1
REQUEST_TIMEOUT = 2
MAX_RECONNECT_ATTEMPTS = 10


def watch_grpc_server_thread(
    location_name: str,
    client: DagsterGrpcClient,
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    on_updated: Callable[[str, str], None],
    on_error: Callable[[str], None],
    needs_location_refresh: Callable[[str, str], bool],
    shutdown_event: threading.Event,
    watch_interval: float | None = None,
    max_reconnect_attempts: int | None = None,
) -> None:
    """This thread watches the state of the unmanaged gRPC server and calls the appropriate handler
    functions in case of a change.

    The following loop polls the GetServerId endpoint to check if either:
    1. The server_id has changed
    2. The server is unreachable

    In the case of (1) The server ID has changed, we call `on_updated` and continue polling.
    The thread does not exit — it keeps monitoring for further changes.

    In the case of (2) The server is unreachable, we attempt to automatically reconnect. If we
    are able to reconnect, there are two possibilities:

    a. The server ID has changed
        -> In this case, we call `on_updated` and resume polling.
    b. The server ID is the same
        -> In this case, we call `on_reconnected`, and we go back to polling the server for
        changes.

    If we are unable to reconnect to the server within the specified max_reconnect_attempts, we
    call on_error. After on_error, the reconnect loop continues indefinitely — the thread does
    not shut down, so that if the server eventually comes back, it will be detected via
    on_updated (not on_reconnected). This is intentional: on_error already notified subscribers
    of the failure, so recovery must go through on_updated to trigger a refresh that clears the
    error state. The stored server ID is cleared on error to ensure the on_updated path is
    taken regardless of whether the actual server ID changed.

    Additionally, if `needs_location_refresh` returns True during normal polling (indicating
    that the workspace entry is in an error state or has a stale version key), `on_disconnect`
    and `on_reconnected` are fired even if the server ID hasn't changed. This enables recovery
    when a prior refresh failed (e.g. during a Kubernetes rolling deployment where the gRPC
    call routed to a dying pod).

    `on_updated` is called each time a server ID change is detected and does not cause the
    thread to exit. `on_error` is called at most once per disconnect cycle but does not cause
    the thread to exit. `on_disconnect` and `on_reconnected` may be called multiple times to
    properly handle intermittent network failures or workspace error recovery. The thread only
    exits when shutdown_event is set.
    """
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)
    check.callable_param(on_disconnect, "on_disconnect")
    check.callable_param(on_reconnected, "on_reconnected")
    check.callable_param(on_updated, "on_updated")
    check.callable_param(on_error, "on_error")
    check.callable_param(needs_location_refresh, "needs_location_refresh")
    watch_interval = check.opt_numeric_param(watch_interval, "watch_interval", WATCH_INTERVAL)
    max_reconnect_attempts = check.opt_int_param(
        max_reconnect_attempts, "max_reconnect_attempts", MAX_RECONNECT_ATTEMPTS
    )

    needs_location_refresh_count = 0
    server_id = {"current": None, "error": False}

    def current_server_id() -> str | None:
        return server_id["current"]

    def has_error() -> bool:
        return server_id["error"]

    def _needs_location_refresh() -> bool:
        current_id = current_server_id()
        result = current_id is not None and needs_location_refresh(location_name, current_id)
        if result:
            nonlocal needs_location_refresh_count
            needs_location_refresh_count += 1
        return result

    def set_server_id(new_id: str) -> None:
        server_id["current"] = new_id
        server_id["error"] = False
        nonlocal needs_location_refresh_count
        needs_location_refresh_count = 0

    def set_error() -> None:
        # Clearing current server ID ensures that post-error recovery always takes
        # the on_updated path in reconnect_loop, which is needed to trigger a
        # refresh that clears the error state in subscribers.
        server_id["current"] = None
        server_id["error"] = True

    def watch_for_changes():
        nonlocal needs_location_refresh_count
        needs_location_refresh_count = 0
        while True:
            if shutdown_event.is_set():
                break

            curr = current_server_id()

            new_server_id = client.get_server_id(timeout=REQUEST_TIMEOUT)
            if curr is None:
                set_server_id(new_server_id)
            elif curr != new_server_id:
                set_server_id(new_server_id)
                on_updated(location_name, new_server_id)
            elif _needs_location_refresh():
                # Wait 2 cycles to confirm the error persists (giving get_server_id() a
                # chance to throw DagsterUserCodeUnreachableError and trigger reconnect_loop
                # instead). After that, retry every 10 cycles to avoid log spam and
                # unnecessary gRPC calls when the location is permanently stuck.
                if (
                    needs_location_refresh_count >= 2
                    and (needs_location_refresh_count - 2) % 10 == 0
                ):
                    # get_server_id() keeps succeeding but _needs_location_refresh() still
                    # returns True. The workspace entry is errored/stale. Fire disconnect +
                    # reconnect callbacks to trigger a recovery refresh.
                    on_disconnect(location_name)
                    on_reconnected(location_name)

            shutdown_event.wait(watch_interval)

    def reconnect_loop():
        attempts = 0
        while True:
            shutdown_event.wait(watch_interval)
            if shutdown_event.is_set():
                return

            try:
                new_server_id = client.get_server_id(timeout=REQUEST_TIMEOUT)
                if current_server_id() == new_server_id and not has_error():
                    # Intermittent failure, was able to reconnect to the same server
                    # before max_reconnect_attempts was exhausted.
                    on_reconnected(location_name)
                    return
                else:
                    # Either the server ID changed, or we're recovering after on_error
                    # was already called. Either way, on_updated triggers a refresh.
                    on_updated(location_name, new_server_id)
                    set_server_id(new_server_id)
                    return
            except DagsterUserCodeUnreachableError:
                attempts += 1

            if attempts >= max_reconnect_attempts and not has_error():
                on_error(location_name)
                set_error()
                # Intentionally does not return — the loop continues so that if the
                # server eventually comes back, it will be detected via on_updated.

    while True:
        if shutdown_event.is_set():
            break
        try:
            watch_for_changes()
        except DagsterUserCodeUnreachableError:
            on_disconnect(location_name)
            reconnect_loop()


def create_grpc_watch_thread(
    location_name: str,
    client: DagsterGrpcClient,
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    on_updated: Callable[[str, str], None],
    on_error: Callable[[str], None],
    needs_location_refresh: Callable[[str, str], bool],
    watch_interval: float | None = None,
    max_reconnect_attempts: int | None = None,
) -> tuple[threading.Event, threading.Thread]:
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)

    check.callable_param(on_disconnect, "on_disconnect")
    check.callable_param(on_reconnected, "on_reconnected")
    check.callable_param(on_updated, "on_updated")
    check.callable_param(on_error, "on_error")
    check.callable_param(needs_location_refresh, "needs_location_refresh")

    shutdown_event = threading.Event()
    thread = threading.Thread(
        target=watch_grpc_server_thread,
        args=[
            location_name,
            client,
            on_disconnect,
            on_reconnected,
            on_updated,
            on_error,
            needs_location_refresh,
            shutdown_event,
            watch_interval,
            max_reconnect_attempts,
        ],
        name="grpc-server-watch",
        daemon=True,
    )
    return shutdown_event, thread
