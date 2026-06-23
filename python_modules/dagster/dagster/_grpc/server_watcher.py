import logging
import threading
from collections.abc import Callable

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.workspace.workspace import CodeLocationEntry
from dagster._grpc.client import DagsterGrpcClient

logger = logging.getLogger("dagster")

WATCH_INTERVAL = 1
REQUEST_TIMEOUT = 2
MAX_RECONNECT_ATTEMPTS = 10


def watch_grpc_server_thread(
    location_name: str,
    client: DagsterGrpcClient,
    shutdown_event: threading.Event,
    *,
    get_location_entry: Callable[[str], CodeLocationEntry | None],
    refresh_code_location: Callable[[str], None],
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    on_updated: Callable[[str, str], None],
    on_error: Callable[[str], None],
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
    call on_error. After on_error fires, the reconnect loop continues indefinitely — if the
    server eventually comes back, recovery is signaled via on_updated rather than on_reconnected,
    so that subscribers receive a state transition that triggers a workspace refresh and clears
    the error. The stored server ID is cleared on error so the on_updated branch is taken
    regardless of whether the actual server ID changed.

    Additionally, if `get_location_entry(location_name).load_error` is a
    `DagsterUserCodeUnreachableError`, this is treated the same as "2. The server is unreachable":
    `on_disconnect` is fired and the reconnect loop runs. This enables recovery when a prior
    refresh failed with a transient gRPC error (e.g. during a Kubernetes rolling deployment where
    the gRPC call routed to a dying pod). The check is intentionally scoped to
    `DagsterUserCodeUnreachableError` only: other load errors (e.g. `DagsterUserCodeProcessError`
    from a syntax error in user code) are treated as non-transient and not retried here, to avoid
    log spam and wasted gRPC traffic on permanently-broken locations. Within the reconnect loop,
    if `GetServerId` succeeds but the workspace entry is still errored, `refresh_code_location`
    is called directly — we don't route this through any `on_*` event, because subscribers should
    only be notified on actual state transitions, not every poll. Once the error clears, the next
    loop iteration fires on_updated and exits the reconnect loop.

    The thread only exits when shutdown_event is set. on_updated, on_disconnect, and
    on_reconnected may fire multiple times over the thread's lifetime; on_error fires at most
    once per disconnect → reconnect-exhausted transition.
    """
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)
    check.callable_param(get_location_entry, "get_location_entry")
    check.callable_param(refresh_code_location, "refresh_code_location")
    check.callable_param(on_disconnect, "on_disconnect")
    check.callable_param(on_reconnected, "on_reconnected")
    check.callable_param(on_updated, "on_updated")
    check.callable_param(on_error, "on_error")
    watch_interval = check.opt_numeric_param(watch_interval, "watch_interval", WATCH_INTERVAL)
    max_reconnect_attempts = check.opt_int_param(
        max_reconnect_attempts, "max_reconnect_attempts", MAX_RECONNECT_ATTEMPTS
    )

    class ServerId:
        current: str | None = None
        error: bool = False

    server_id = ServerId()

    def current_server_id() -> str | None:
        return server_id.current

    def has_error() -> bool:
        return server_id.error

    def update_server_id(new_id: str, send_on_updated_event: bool = True) -> None:
        server_id.current = new_id
        server_id.error = False
        if send_on_updated_event:
            on_updated(location_name, new_id)

    def set_error() -> None:
        # Clearing current server ID forces the on_updated branch on recovery
        server_id.current = None
        server_id.error = True

    def get_location_entry_or_raise_unreachable_error() -> CodeLocationEntry | None:
        location_entry = get_location_entry(location_name)
        if location_entry is None:
            return None
        load_error = location_entry.load_error
        if (
            load_error is not None
            and load_error.cls_name == DagsterUserCodeUnreachableError.__name__
        ):
            raise DagsterUserCodeUnreachableError(load_error.to_string())
        return location_entry

    def watch_for_changes() -> None:
        while True:
            if shutdown_event.is_set():
                break

            curr: str | None = current_server_id()

            new_server_id: str = client.get_server_id(timeout=REQUEST_TIMEOUT)
            if curr != new_server_id:
                update_server_id(new_server_id, send_on_updated_event=(curr is not None))
            else:
                _ = get_location_entry_or_raise_unreachable_error()

            shutdown_event.wait(watch_interval)

    def reconnect_loop() -> None:
        attempts = 0
        while True:
            shutdown_event.wait(watch_interval)
            if shutdown_event.is_set():
                return

            location_unreachable_error: DagsterUserCodeUnreachableError | None = None

            try:
                new_server_id = client.get_server_id(timeout=REQUEST_TIMEOUT)
                curr = current_server_id()
                if curr != new_server_id and not has_error():
                    # A new server ID is sufficient signal to recover: the on_updated event
                    # triggers a workspace refresh that clears any stale load_error. If that
                    # refresh fails, the next watch_for_changes() poll puts us back here.
                    update_server_id(new_server_id)
                    return
                try:
                    _ = get_location_entry_or_raise_unreachable_error()
                except DagsterUserCodeUnreachableError as exc:
                    location_unreachable_error = exc
                    raise
                if curr == new_server_id and not has_error():
                    # Intermittent failure, was able to reconnect to the same server
                    # before max_reconnect_attempts was exhausted.
                    on_reconnected(location_name)
                    return
                else:
                    # Recovering after on_error already fired (has_error() is True so curr is
                    # None). Fire on_updated to trigger a workspace refresh. The
                    # unreachable-error check above has already verified the workspace entry
                    # is healthy, so we won't flap.
                    update_server_id(new_server_id)
                    return
            except DagsterUserCodeUnreachableError:
                attempts += 1

            if attempts >= max_reconnect_attempts and not has_error():
                on_error(location_name)
                set_error()
                # Do not return: keep looping so that an eventual recovery is detected
                # via on_updated (see module docstring).
            elif location_unreachable_error is not None and (
                attempts % max_reconnect_attempts == 0 or not has_error()
            ):
                # GetServerId succeeds but the workspace entry stays errored. Retry every poll
                # before on_error fires (fast recovery), then back off to one retry per
                # max_reconnect_attempts cycles — spacing out retries on persistently-stuck
                # locations avoids log spam, excess gRPC traffic, and repeated wasted refresh
                # work that we already know is likely to fail again.
                refresh_code_location(location_name)

    while True:
        do_reconnect_loop = False
        if shutdown_event.is_set():
            break
        try:
            watch_for_changes()
        except DagsterUserCodeUnreachableError:
            if shutdown_event.is_set():
                break
            do_reconnect_loop = True
            try:
                on_disconnect(location_name)
            except Exception as exc:
                logger.exception(
                    f"In gRPC watch server thread for location {location_name}, on_disconnect raised {exc.__class__.__name__}: {exc}"
                )
        except Exception as exc:
            logger.exception(
                f"In gRPC watch server thread for location {location_name}, watch_for_changes raised {exc.__class__.__name__}: {exc}"
            )
            shutdown_event.wait(watch_interval * max_reconnect_attempts)
        while do_reconnect_loop:
            try:
                reconnect_loop()
            except Exception as exc:
                logger.exception(
                    f"In gRPC watch server thread for location {location_name}, reconnect_loop raised {exc.__class__.__name__}: {exc}"
                )
                shutdown_event.wait(watch_interval * max_reconnect_attempts)
            else:
                do_reconnect_loop = False


def create_grpc_watch_thread(
    location_name: str,
    client: DagsterGrpcClient,
    *,
    get_location_entry: Callable[[str], CodeLocationEntry | None],
    refresh_code_location: Callable[[str], None],
    on_disconnect: Callable[[str], None],
    on_reconnected: Callable[[str], None],
    on_updated: Callable[[str, str], None],
    on_error: Callable[[str], None],
    watch_interval: float | None = None,
    max_reconnect_attempts: int | None = None,
) -> tuple[threading.Event, threading.Thread]:
    """Create a daemon thread that watches a gRPC server for changes.

    Returns a (shutdown_event, thread) tuple. Set shutdown_event to stop the thread. The thread
    is a daemon and must be started by the caller via thread.start().

    See watch_grpc_server_thread for full documentation of the callback semantics.
    """
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)

    check.callable_param(get_location_entry, "get_location_entry")
    check.callable_param(refresh_code_location, "refresh_code_location")
    check.callable_param(on_disconnect, "on_disconnect")
    check.callable_param(on_reconnected, "on_reconnected")
    check.callable_param(on_updated, "on_updated")
    check.callable_param(on_error, "on_error")

    shutdown_event = threading.Event()
    thread = threading.Thread(
        target=lambda: watch_grpc_server_thread(
            location_name,
            client,
            shutdown_event=shutdown_event,
            get_location_entry=get_location_entry,
            refresh_code_location=refresh_code_location,
            on_disconnect=on_disconnect,
            on_reconnected=on_reconnected,
            on_updated=on_updated,
            on_error=on_error,
            watch_interval=watch_interval,
            max_reconnect_attempts=max_reconnect_attempts,
        ),
        name="grpc-server-watch",
        daemon=True,
    )
    return shutdown_event, thread
