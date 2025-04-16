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
        }
    }
}
"""


@asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )
)
def asset_with_internal_freshness_policy_with_warn_window():
    pass


@asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=10))
)
def asset_with_internal_freshness_policy():
    pass


def get_repo() -> RepositoryDefinition:
    return Definitions(
        assets=[
            asset_with_internal_freshness_policy,
            asset_with_internal_freshness_policy_with_warn_window,
        ]
    ).get_repository_def()


def test_internal_freshness_policy_time_window():
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as graphql_context:
            result = execute_dagster_graphql(
                graphql_context,
                GET_INTERNAL_FRESHNESS_POLICY,
                variables={"assetKey": asset_with_internal_freshness_policy.key.to_graphql_input()},
            )
            assert result.data["assetNodes"][0]["internalFreshnessPolicy"] == {
                "failWindowSeconds": 600,
                "warnWindowSeconds": None,
            }


def test_internal_freshness_policy_time_window_with_warn_window():
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as graphql_context:
            result = execute_dagster_graphql(
                graphql_context,
                GET_INTERNAL_FRESHNESS_POLICY,
                variables={
                    "assetKey": asset_with_internal_freshness_policy_with_warn_window.key.to_graphql_input()
                },
            )
            assert result.data["assetNodes"][0]["internalFreshnessPolicy"] == {
                "failWindowSeconds": 600,
                "warnWindowSeconds": 300,
            }
