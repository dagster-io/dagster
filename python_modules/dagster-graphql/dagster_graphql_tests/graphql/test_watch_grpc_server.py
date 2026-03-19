import time
from typing import Any

from dagster._core.remote_representation.grpc_server_state_subscriber import (
    LocationStateChangeEventType,
    LocationStateSubscriber,
)
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    DefinitionsSource,
)
from dagster._utils.error import SerializableErrorInfo

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
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

        error_events = [
            e for e in events if e.event_type == LocationStateChangeEventType.LOCATION_ERROR
        ]
        assert len(error_events) == 1
        assert error_events[0].location_name == location.name

        # LOCATION_DISCONNECTED should have arrived before LOCATION_ERROR
        disconnect_events = [
            e for e in events if e.event_type == LocationStateChangeEventType.LOCATION_DISCONNECTED
        ]
        assert len(disconnect_events) == 1
        assert disconnect_events[0].location_name == location.name


RecoveryTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()]
)


class TestGrpcServerRecovery(RecoveryTestSuite):
    def test_grpc_server_recovery_after_failed_refresh(self, graphql_context):
        """Integration test: verify that the watch thread triggers recovery when a code location
        is stuck in an error state after a failed refresh.

        This simulates the K8s rolling deployment race condition end-to-end:
        1. Directly set the workspace entry to an errored state (simulating a failed refresh)
        2. Verify the watch thread detects the error via _should_recover_location
        3. Verify it fires on_disconnect + on_reconnected events
        4. Verify the event handler calls refresh_code_location (which now succeeds)
        5. Verify the location recovers
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
        # This is what happens when _load_location fails during the race condition.
        current_entry = ctx.get_current_workspace().code_location_entries[location_name]
        errored_entry = CodeLocationEntry(
            origin=current_entry.origin,
            code_location=None,
            load_error=SerializableErrorInfo("Simulated failure", [], "RuntimeError"),
            load_status=CodeLocationLoadStatus.LOADED,
            display_metadata=current_entry.origin.get_display_metadata(),
            update_timestamp=0.0,
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

        # The watch thread should detect the error via _should_recover_location and fire
        # on_disconnect + on_reconnected, which flows through _location_state_events_handler
        # and triggers refresh_code_location, recovering the location.
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

        # Verify the recovery events were fired
        disconnect_events = [
            e for e in events if e.event_type == LocationStateChangeEventType.LOCATION_DISCONNECTED
        ]
        reconnected_events = [
            e for e in events if e.event_type == LocationStateChangeEventType.LOCATION_RECONNECTED
        ]
        assert len(disconnect_events) >= 1
        assert len(reconnected_events) >= 1
