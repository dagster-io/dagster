import logging
import threading
import time
from collections.abc import Callable

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.workspace.workspace import CodeLocationEntry
from dagster._grpc.client import DagsterGrpcClient

logger = logging.getLogger("dagster")

WATCH_INTERVAL = 1
REQUEST_TIMEOUT = 2
MAX_RECONNECT_ATTEMPTS = 10
# How often to check whether the location is stuck in a transient unreachable-error state and, if
# so, attempt a recovery refresh. Deliberately independent of WATCH_INTERVAL: the server-id poll
# runs frequently to detect server changes quickly, while the recovery check runs on a slower,
# fixed cadence because refreshing an errored location is comparatively expensive and a stuck
# location rarely recovers within a single second.
ERROR_RECOVERY_INTERVAL = 10


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
    error_recovery_interval: float | None = None,
) -> None:
    """This thread watches the state of the unmanaged gRPC server and calls the appropriate handler
    functions in case of a change.

    Two independent concerns run on this single thread:

    1. Server-id watching (the gRPC loop). The thread polls the GetServerId endpoint to check if
    either:
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
        server eventually comes back, recovery is signaled via on_updated rather than
        on_reconnected, so that subscribers receive a state transition that triggers a workspace
        refresh and clears the error. The stored server ID is cleared on error so the on_updated
        branch is taken regardless of whether the actual server ID changed.

    2. Error recovery (a separate, fixed-cadence check). Every `error_recovery_interval` seconds,
    the thread inspects `get_location_entry(location_name).load_error`. If it is a
    `DagsterUserCodeUnreachableError`, the thread calls `refresh_code_location` directly to attempt
    to clear it. This recovers a location whose prior refresh failed with a transient gRPC error
    (e.g. during a Kubernetes rolling deployment where the gRPC call routed to a dying pod) but
    whose server is otherwise reachable — a state the server-id watch above does not detect,
    because GetServerId keeps succeeding. This check is intentionally separate from the server-id
    watch/reconnect logic and never fires any `on_*` event: it only refreshes the workspace, and
    the refresh itself emits whatever state events are warranted. The check is scoped to
    `DagsterUserCodeUnreachableError` only: other load errors (e.g. `DagsterUserCodeProcessError`
    from a syntax error in user code) are treated as non-transient and not retried here, to avoid
    log spam and wasted gRPC traffic on permanently-broken locations.

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
    error_recovery_interval = check.opt_numeric_param(
        error_recovery_interval, "error_recovery_interval", ERROR_RECOVERY_INTERVAL
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

    def attempt_error_recovery() -> None:
        """Refresh the location if it is stuck in a transient unreachable-error state.

        Runs on its own fixed cadence, independent of the server-id watch/reconnect logic. Does
        not fire any on_* event — the refresh itself emits whatever state events are warranted.
        """
        location_entry = get_location_entry(location_name)
        if location_entry is None:
            return
        load_error = location_entry.load_error
        if load_error is None or load_error.cls_name != DagsterUserCodeUnreachableError.__name__:
            return

        logger.info(
            f"Location {location_name} is stuck in a transient unreachable-error state; "
            "attempting a recovery refresh"
        )
        try:
            refresh_code_location(location_name)
        except Exception as exc:
            logger.exception(
                f"In gRPC watch server thread for location {location_name}, recovery refresh "
                f"raised {exc.__class__.__name__}: {exc}"
            )

    def watch_for_changes() -> None:
        last_recovery_check = time.monotonic()
        while True:
            if shutdown_event.is_set():
                break

            curr: str | None = current_server_id()

            new_server_id: str = client.get_server_id(timeout=REQUEST_TIMEOUT)
            if curr != new_server_id:
                update_server_id(new_server_id, send_on_updated_event=(curr is not None))

            now = time.monotonic()
            if now - last_recovery_check >= error_recovery_interval:
                last_recovery_check = now
                attempt_error_recovery()

            shutdown_event.wait(watch_interval)

    def reconnect_loop() -> None:
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
                    # Either the server ID changed or we are recovering after on_error already
                    # fired (has_error() is True so current is None). Fire on_updated to trigger a
                    # workspace refresh.
                    update_server_id(new_server_id)
                    return
            except DagsterUserCodeUnreachableError:
                attempts += 1

            if attempts >= max_reconnect_attempts and not has_error():
                on_error(location_name)
                set_error()
                # Do not return: keep looping so that an eventual recovery is detected
                # via on_updated (see above).

    while True:
        if shutdown_event.is_set():
            break
        try:
            watch_for_changes()
        except DagsterUserCodeUnreachableError:
            if shutdown_event.is_set():
                break
            try:
                on_disconnect(location_name)
            except Exception as exc:
                logger.exception(
                    f"In gRPC watch server thread for location {location_name}, on_disconnect raised {exc.__class__.__name__}: {exc}"
                )
            try:
                reconnect_loop()
            except Exception as exc:
                logger.exception(
                    f"In gRPC watch server thread for location {location_name}, reconnect_loop raised {exc.__class__.__name__}: {exc}"
                )
                shutdown_event.wait(watch_interval * max_reconnect_attempts)
        except Exception as exc:
            logger.exception(
                f"In gRPC watch server thread for location {location_name}, watch_for_changes raised {exc.__class__.__name__}: {exc}"
            )
            shutdown_event.wait(watch_interval * max_reconnect_attempts)


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
    error_recovery_interval: float | None = None,
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
            error_recovery_interval=error_recovery_interval,
        ),
        name="grpc-server-watch",
        daemon=True,
    )
    return shutdown_event, thread
