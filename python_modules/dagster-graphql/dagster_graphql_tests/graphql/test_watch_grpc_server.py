import time
from typing import Any
from unittest.mock import patch

from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.remote_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    DefinitionsSource,
)
from dagster._grpc import server_watcher
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server_watcher import MAX_RECONNECT_ATTEMPTS
from dagster._utils.error import SerializableErrorInfo

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    graphql_context_variants_fixture,
    make_graphql_context_test_suite,
)

BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()]
)


class TestSubscribeToGrpcServerEvents(BaseTestSuite):
    def test_grpc_server_handle_message_subscription(self, graphql_context):
        events = []
        test_subscriber = LocationStateSubscriber(events.append)
        location = next(
            iter(graphql_context.process_context.create_request_context().code_locations)
        )
        graphql_context.process_context.add_state_subscriber(test_subscriber)
        location.client.shutdown_server()

        # Wait for LOCATION_ERROR event. LOCATION_DISCONNECTED may arrive first since the
        # watch thread detects the disconnect before exhausting reconnect attempts.
        start_time = time.time()
        timeout = 60
        while not any(e.event_type == LocationStateChangeEventType.LOCATION_ERROR for e in events):
            if time.time() - start_time > timeout:
                raise Exception("Timed out waiting for LOCATION_ERROR event")
            time.sleep(1)

        error_events = _events_of_type(events, LocationStateChangeEventType.LOCATION_ERROR)
        assert len(error_events) == 1
        assert error_events[0].location_name == location.name

        # The watch thread fires LOCATION_DISCONNECTED on the first failed poll, then
        # LOCATION_ERROR once reconnect attempts are exhausted. Both events should be present
        # by the time we observe LOCATION_ERROR.
        disconnect_events = _events_of_type(
            events, LocationStateChangeEventType.LOCATION_DISCONNECTED
        )
        assert len(disconnect_events) == 1
        assert disconnect_events[0].location_name == location.name


RECOVERY_CONTEXT_VARIANTS = [
    GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()
]
RecoveryTestSuite: Any = make_graphql_context_test_suite(context_variants=RECOVERY_CONTEXT_VARIANTS)


class TestGrpcServerRecovery(RecoveryTestSuite):
    @graphql_context_variants_fixture(context_variants=RECOVERY_CONTEXT_VARIANTS)
    def yield_class_scoped_graphql_context(self, request):
        with patch.object(server_watcher, "WATCH_INTERVAL", 0.1):
            with self.graphql_context_for_request(request) as graphql_context:
                yield graphql_context

    def test_grpc_server_recovery_after_failed_refresh(self, graphql_context):
        """Integration test: verify that the watch thread triggers recovery when a code location
        is stuck in an error state after a failed refresh.

        This simulates the K8s rolling deployment race condition end-to-end:
        1. Directly set the workspace entry to an errored state with a
           DagsterUserCodeUnreachableError load_error (simulating a failed refresh against a
           pod that was briefly unreachable).
        2. The watch thread's polling call to get_location_entry_or_raise_unreachable_error()
           sees the unreachable load_error and re-raises DagsterUserCodeUnreachableError, which
           kicks watch_for_changes() out to the outer reconnect path.
        3. on_disconnect fires and reconnect_loop runs. Because GetServerId still succeeds
           against the live server but the workspace entry remains errored, reconnect_loop
           calls refresh_code_location directly to clear the stuck error.
        4. Once refresh_code_location succeeds, the next iteration of reconnect_loop sees a
           healthy entry and matching server ID, and fires on_reconnected.
        5. Verify the location recovers.
        """
        ctx = graphql_context.process_context
        location = next(iter(ctx.create_request_context().code_locations))
        location_name = location.name

        events = []
        test_subscriber = LocationStateSubscriber(events.append)
        ctx.add_state_subscriber(test_subscriber)

        # Verify location starts healthy
        assert not ctx.has_code_location_error(location_name)

        # Simulate a failed refresh by directly setting the workspace entry to an errored state.
        # The load_error must be a DagsterUserCodeUnreachableError: that is the only error class
        # that get_location_entry_or_raise_unreachable_error() in the watch thread will re-raise
        # to trigger the reconnect/recovery path.
        current_entry = ctx.get_current_workspace().code_location_entries[location_name]
        injected_timestamp = time.time()
        errored_entry = CodeLocationEntry(
            origin=current_entry.origin,
            code_location=None,
            load_error=SerializableErrorInfo(
                "Simulated unreachable failure", [], "DagsterUserCodeUnreachableError"
            ),
            load_status=CodeLocationLoadStatus.LOADED,
            display_metadata=current_entry.origin.get_display_metadata(),
            update_timestamp=injected_timestamp,
            version_key="stale-version-key",
            definitions_source=DefinitionsSource.CODE_SERVER,
        )
        with ctx._lock:  # noqa: SLF001
            ctx._current_workspace = (  # noqa: SLF001
                ctx._current_workspace.with_code_location(  # noqa: SLF001
                    location_name, errored_entry
                )
            )

        # Verify location is now errored
        assert ctx.has_code_location_error(location_name)

        # The watch thread should detect the unreachable load_error, fire on_disconnect, enter
        # reconnect_loop, and call refresh_code_location directly to clear the stuck error.
        # Once the refresh succeeds, reconnect_loop fires on_reconnected on its next iteration.
        start_time = time.time()
        timeout = 30
        while ctx.has_code_location_error(location_name):
            if time.time() - start_time > timeout:
                raise Exception(
                    f"Timed out waiting for location {location_name} to recover. "
                    f"Events received: {[(e.event_type, e.location_name) for e in events]}"
                )
            time.sleep(0.5)

        # Location should be recovered — no longer errored, code_location is set
        assert not ctx.has_code_location_error(location_name)
        assert ctx.has_code_location(location_name)
        recovered_entry = ctx.get_current_workspace().code_location_entries[location_name]
        assert recovered_entry.update_timestamp > injected_timestamp

        # Wait for on_reconnected: refresh_code_location clears the error inline within
        # reconnect_loop, but on_reconnected fires on the *next* poll iteration once the entry
        # check passes and GetServerId matches the cached server id.
        start_time = time.time()
        reconnect_timeout = 30
        while not _events_of_type(events, LocationStateChangeEventType.LOCATION_RECONNECTED):
            if time.time() - start_time > reconnect_timeout:
                raise Exception(
                    f"Timed out waiting for LOCATION_RECONNECTED event for {location_name}. "
                    f"Events received: {[(e.event_type, e.location_name) for e in events]}"
                )
            time.sleep(0.5)

        # Verify the recovery events were fired
        disconnect_events = _events_of_type(
            events, LocationStateChangeEventType.LOCATION_DISCONNECTED
        )
        reconnected_events = _events_of_type(
            events, LocationStateChangeEventType.LOCATION_RECONNECTED
        )
        assert len(disconnect_events) >= 1
        assert len(reconnected_events) >= 1

    def test_grpc_server_on_error_then_recovery_via_on_updated(self, graphql_context):
        """Integration test: when reconnect attempts exhaust MAX_RECONNECT_ATTEMPTS, on_error
        fires once and the stored server id is cleared. Recovery (once the server is reachable
        again) is then signaled via on_updated rather than on_reconnected — the watch thread
        deliberately routes through on_updated so that the workspace event handler triggers a
        refresh and clears the error state.

        This complements test_grpc_server_recovery_after_failed_refresh, which exercises the
        pre-on_error path. Here we exercise the post-on_error path.
        """
        ctx = graphql_context.process_context
        location = next(iter(ctx.create_request_context().code_locations))
        location_name = location.name

        events = []
        test_subscriber = LocationStateSubscriber(events.append)
        ctx.add_state_subscriber(test_subscriber)

        # Patch DagsterGrpcClient.get_server_id at the class level to raise
        # DagsterUserCodeUnreachableError for enough polls that the watch thread exhausts its
        # reconnect budget and fires on_error, then releases so the next poll succeeds and
        # on_updated fires. The class-level patch is safe because (a) no workspace refresh runs
        # while the patch is active — refresh_code_location is only invoked by the on_updated
        # handler, which runs after the patch is released — and (b) the with-block scopes
        # cleanup tightly.
        real_get_server_id = DagsterGrpcClient.get_server_id
        # Fail just past MAX_RECONNECT_ATTEMPTS to guarantee on_error fires before recovery.
        failure_budget = MAX_RECONNECT_ATTEMPTS + 2
        call_count = {"n": 0}

        def flaky_get_server_id(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] <= failure_budget:
                raise DagsterUserCodeUnreachableError("simulated outage")
            return real_get_server_id(self, *args, **kwargs)

        with patch.object(DagsterGrpcClient, "get_server_id", flaky_get_server_id):
            # Wait for LOCATION_ERROR — fires after MAX_RECONNECT_ATTEMPTS consecutive failures.
            start_time = time.time()
            timeout = 60
            while not _events_of_type(events, LocationStateChangeEventType.LOCATION_ERROR):
                if time.time() - start_time > timeout:
                    raise Exception(
                        f"Timed out waiting for LOCATION_ERROR event for {location_name}. "
                        f"Events received: {[(e.event_type, e.location_name) for e in events]}"
                    )
                time.sleep(0.5)

        # Patch released — the next successful poll should fire LOCATION_UPDATED (not
        # LOCATION_RECONNECTED) because set_error() cleared the stored server id.
        start_time = time.time()
        timeout = 30
        while not _events_of_type(events, LocationStateChangeEventType.LOCATION_UPDATED):
            if time.time() - start_time > timeout:
                raise Exception(
                    f"Timed out waiting for LOCATION_UPDATED event for {location_name}. "
                    f"Events received: {[(e.event_type, e.location_name) for e in events]}"
                )
            time.sleep(0.5)

        disconnect_events = _events_of_type(
            events, LocationStateChangeEventType.LOCATION_DISCONNECTED
        )
        error_events = _events_of_type(events, LocationStateChangeEventType.LOCATION_ERROR)
        updated_events = _events_of_type(events, LocationStateChangeEventType.LOCATION_UPDATED)
        reconnected_events = _events_of_type(
            events, LocationStateChangeEventType.LOCATION_RECONNECTED
        )

        assert len(disconnect_events) == 1
        assert len(error_events) == 1
        assert len(updated_events) >= 1
        # Crucial: recovery after on_error must NOT fire on_reconnected — it must route through
        # on_updated so the workspace handler triggers a refresh.
        assert len(reconnected_events) == 0


def _events_of_type(
    events: list[LocationStateChangeEvent], event_type: LocationStateChangeEventType
) -> list[LocationStateChangeEvent]:
    return [e for e in events if e.event_type == event_type]
