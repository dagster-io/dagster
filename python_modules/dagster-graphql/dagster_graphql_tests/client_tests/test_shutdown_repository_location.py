import time

import grpc
from dagster_graphql import ShutdownRepositoryLocationStatus

from ..graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)


class TestShutdownRepositoryLocation(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()]
    )
):
    def test_shutdown_repository_location(self, graphql_client, graphql_context):
        origin = next(iter(graphql_context.workspace_snapshot.values())).origin
        origin.create_client().heartbeat()

        result = graphql_client.shutdown_repository_location("test")

        assert result.status == ShutdownRepositoryLocationStatus.SUCCESS, result.message

        # Wait for client to be unavailable
        start_time = time.time()

        while time.time() - start_time < 15:
            try:
                origin.create_client().heartbeat()
            except grpc._channel._InactiveRpcError:  # pylint:disable=protected-access
                # Shutdown succeeded
                return
            time.sleep(1)

        raise Exception("Timed out waiting for shutdown to take effect")

    def test_shutdown_repository_location_not_found(self, graphql_client):
        result = graphql_client.shutdown_repository_location("not_real")

        assert result.status == ShutdownRepositoryLocationStatus.FAILURE
        assert "Location not_real does not exist" in result.message
