import time

from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite


class TestSubscribeToGrpcServerEvents(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()]
    )
):
    def test_grpc_server_handle_message_subscription(self, graphql_context):
        events = []
        test_subscriber = LocationStateSubscriber(events.append)
        location = next(
            iter(
                graphql_context.process_context.create_request_context().repository_locations  # pylint: disable=protected-access
            )
        )
        graphql_context.process_context.add_state_subscriber(  # pylint: disable=protected-access
            test_subscriber
        )
        location.client.shutdown_server()

        # Wait for event
        start_time = time.time()
        timeout = 60
        while not len(events) > 0:
            if time.time() - start_time > timeout:
                raise Exception("Timed out waiting for LocationStateChangeEvent")
            time.sleep(1)

        assert len(events) == 1
        assert isinstance(events[0], LocationStateChangeEvent)
        assert events[0].event_type == LocationStateChangeEventType.LOCATION_ERROR
        assert events[0].location_name == location.name
