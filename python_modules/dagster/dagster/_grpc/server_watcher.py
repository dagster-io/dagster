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
    call on_error. After on_error, the reconnect loop continues indefinitely — the thread does
    not shut down, so that if the server eventually comes back, it will be detected via
    on_updated (not on_reconnected). This is intentional: on_error already notified subscribers
    of the failure, so recovery must go through on_updated to trigger a refresh that clears the
    error state. The stored server ID is cleared on error to ensure the on_updated path is
    taken regardless of whether the actual server ID changed.

    Additionally, if `get_location_entry(location_name).load_error` is a
    `DagsterUserCodeUnreachableError`, this is treated the same as "2. The server is unreachable":
    `on_disconnect` is fired, and the reconnect loop is executed. This enables recovery when a prior
    refresh failed (e.g. during a Kubernetes rolling deployment where the gRPC call routed to a
    dying pod). To avoid flapping, the reconnect loop continues until both GetServerId and the
    refresh succeed without any `DagsterUserCodeUnreachableError`.

    Within the reconnect loop, we call `GetServerId` to test basic connectivity and to observe
    changes to the server_id. If basic connectivity is successful but a
    `DagsterUserCodeUnreachableError` `load_error` is still present, we call `refresh_code_location`
    directly to attempt to clear the error. We don't do this via any `on_*()` event handles, because
    we only want to signal event subscribers on actual changes to the state, not on every loop. If
    the error is cleared, then the next run through the loop will likely end up calling `on_updated`
    and exiting the reconnect loop.

    `on_updated` is called each time a server ID change is detected and does not cause the
    thread to exit. `on_error` is called at most once per `reconnect_loop` invocation (i.e. once
    per transition from connected to disconnected) and does not cause the thread to exit.
    `on_disconnect` and `on_reconnected` may be called multiple times to properly handle
    intermittent network failures or workspace error recovery. The thread only exits when
    shutdown_event is set.
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
                    # NOTE: We deliberately do not gate this branch through
                    # get_location_entry_or_raise_unreachable_error() — a new server ID is by
                    # itself sufficient signal that the upstream changed, and the resulting
                    # on_updated event will trigger a workspace refresh in the event handler
                    # which will clear any stale load_error. If that refresh itself fails, the
                    # next watch_for_changes() poll will re-raise and put us back in this loop.
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
                    # Either the server ID changed, or we're recovering after on_error was
                    # already fired. Fire on_updated (via update_server_id) to trigger a
                    # workspace refresh and exit the reconnect loop. Flapping is prevented by
                    # the get_location_entry_or_raise_unreachable_error() call above, which
                    # would have raised and skipped this branch if the workspace entry were
                    # still stuck on a DagsterUserCodeUnreachableError.
                    update_server_id(new_server_id)
                    return
            except DagsterUserCodeUnreachableError:
                attempts += 1

            if attempts >= max_reconnect_attempts and not has_error():
                on_error(location_name)
                set_error()
                # Intentionally does not return — the loop continues so that if the
                # server eventually comes back, it will be detected via on_updated.
            elif location_unreachable_error is not None and (
                attempts % max_reconnect_attempts == 0 or not has_error()
            ):
                # get_server_id() keeps succeeding but the workspace entry is errored/stale.
                #
                # Before on_error has fired (`not has_error()`), retry recovery on every poll
                # to attempt quick recovery. After on_error has fired, retry every
                # max_reconnect_attempts poll cycles — spacing out retries avoids log spam and
                # unnecessary gRPC calls when a location is persistently stuck.
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
