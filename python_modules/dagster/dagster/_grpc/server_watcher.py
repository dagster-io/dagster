import threading

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._grpc.client import DagsterGrpcClient

WATCH_INTERVAL = 1
REQUEST_TIMEOUT = 2
MAX_RECONNECT_ATTEMPTS = 10


def watch_grpc_server_thread(
    location_name,
    client,
    on_disconnect,
    on_reconnected,
    on_updated,
    on_error,
    shutdown_event,
    watch_interval=None,
    max_reconnect_attempts=None,
):
    """This thread watches the state of the unmanaged gRPC server and calls the appropriate handler
    functions in case of a change.

    The following loop polls the GetServerId endpoint to check if either:
    1. The server_id has changed
    2. The server is unreachable

    In the case of (1) The server ID has changed, we call `on_updated` and end the thread.

    In the case of (2) The server is unreachable, we attempt to automatically reconnect. If we
    are able to reconnect, there are two possibilities:

    a. The server ID has changed
        -> In this case, we we call `on_updated` and end the thread.
    b. The server ID is the same
        -> In this case, we we call `on_reconnected`, and we go back to polling the server for
        changes.

    If we are unable to reconnect to the server within the specified max_reconnect_attempts, we
    call on_error.

    Once the on_updated or on_error events are called, this thread shuts down completely. These two
    events are called at most once, while `on_disconnected` and `on_reconnected` may be called
    multiple times in order to be properly handle intermittent network failures.
    """
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)
    check.callable_param(on_disconnect, "on_disconnect")
    check.callable_param(on_reconnected, "on_reconnected")
    check.callable_param(on_updated, "on_updated")
    check.callable_param(on_error, "on_error")
    watch_interval = check.opt_numeric_param(watch_interval, "watch_interval", WATCH_INTERVAL)
    max_reconnect_attempts = check.opt_int_param(
        max_reconnect_attempts, "max_reconnect_attempts", MAX_RECONNECT_ATTEMPTS
    )

    server_id = {"current": None, "error": False}

    def current_server_id():
        return server_id["current"]

    def has_error():
        return server_id["error"]

    def set_server_id(new_id):
        server_id["current"] = new_id
        server_id["error"] = False

    def set_error():
        server_id["current"] = None
        server_id["error"] = True

    def watch_for_changes():
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
                    on_reconnected(location_name)
                    return
                else:
                    on_updated(location_name, new_server_id)
                    set_server_id(new_server_id)
                    return
            except DagsterUserCodeUnreachableError:
                attempts += 1

            if attempts >= max_reconnect_attempts and not has_error():
                on_error(location_name)
                set_error()

    while True:
        if shutdown_event.is_set():
            break
        try:
            watch_for_changes()
        except DagsterUserCodeUnreachableError:
            on_disconnect(location_name)
            reconnect_loop()


def create_grpc_watch_thread(
    location_name,
    client,
    on_disconnect=None,
    on_reconnected=None,
    on_updated=None,
    on_error=None,
    watch_interval=None,
    max_reconnect_attempts=None,
):
    check.str_param(location_name, "location_name")
    check.inst_param(client, "client", DagsterGrpcClient)

    noop = lambda *a: None
    on_disconnect = check.opt_callable_param(on_disconnect, "on_disconnect", noop)
    on_reconnected = check.opt_callable_param(on_reconnected, "on_reconnected", noop)
    on_updated = check.opt_callable_param(on_updated, "on_updated", noop)
    on_error = check.opt_callable_param(on_error, "on_error", noop)

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
            shutdown_event,
            watch_interval,
            max_reconnect_attempts,
        ],
        name="grpc-server-watch",
    )
    thread.daemon = True
    return shutdown_event, thread
