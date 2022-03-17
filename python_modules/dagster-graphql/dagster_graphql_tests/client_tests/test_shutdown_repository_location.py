import time
from typing import Any

from dagster_graphql import ShutdownRepositoryLocationStatus

from dagster.core.errors import DagsterUserCodeUnreachableError

from ..graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)

BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_deployed_grpc_env()]
)


class TestShutdownRepositoryLocation(BaseTestSuite):
    def test_shutdown_repository_location(self, graphql_client, graphql_context):
        origin = next(iter(graphql_context.get_workspace_snapshot().values())).origin
        origin.create_client().heartbeat()

        result = graphql_client.shutdown_repository_location("test")

        assert result.status == ShutdownRepositoryLocationStatus.SUCCESS, result.message

        # Wait for client to be unavailable
        start_time = time.time()

        while time.time() - start_time < 15:
            try:
                origin.create_client().heartbeat()
            except DagsterUserCodeUnreachableError:
                # Shutdown succeeded
                return
            time.sleep(1)

        raise Exception("Timed out waiting for shutdown to take effect")

    def test_shutdown_repository_location_not_found(self, graphql_client):
        result = graphql_client.shutdown_repository_location("not_real")

        assert result.status == ShutdownRepositoryLocationStatus.FAILURE
        assert "Location not_real does not exist" in result.message
