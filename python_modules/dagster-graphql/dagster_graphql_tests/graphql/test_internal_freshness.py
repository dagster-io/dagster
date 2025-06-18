from datetime import timedelta

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

GET_INTERNAL_FRESHNESS_POLICY = """
query GetInternalFreshnessPolicy($assetKey: AssetKeyInput!) {
    assetNodes(assetKeys: [$assetKey]) {
        internalFreshnessPolicy {
            ... on TimeWindowFreshnessPolicy {
                failWindowSeconds
                warnWindowSeconds
            }
            ... on CronFreshnessPolicy {
                deadlineCron
                lowerBoundDeltaSeconds
                timezone
            }
        }
    }
}
"""


@asset(
    freshness=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )
)
def asset_with_freshness_with_warn_window():
    pass


@asset(freshness=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=10)))
def asset_with_freshness():
    pass


def get_repo() -> RepositoryDefinition:
    return Definitions(
        assets=[
            asset_with_freshness,
            asset_with_freshness_with_warn_window,
        ]
    ).get_repository_def()


# There is a separate implementation for plus graphql tests.
def test_freshness():
    with instance_for_test() as instance:
        assert not instance.internal_asset_freshness_enabled()
        with define_out_of_process_context(__file__, "get_repo", instance) as graphql_context:
            result = execute_dagster_graphql(
                graphql_context,
                GET_INTERNAL_FRESHNESS_POLICY,
                variables={"assetKey": asset_with_freshness.key.to_graphql_input()},
            )
            assert result.data["assetNodes"][0]["internalFreshnessPolicy"] is not None
            result = execute_dagster_graphql(
                graphql_context,
                """
query getFreshnessEnabled {
    instance {
        freshnessEvaluationEnabled
    }
}
                """,
                variables={},
            )
            assert result.data["instance"]["freshnessEvaluationEnabled"] is False
