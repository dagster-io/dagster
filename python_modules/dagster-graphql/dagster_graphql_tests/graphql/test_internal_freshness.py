from datetime import timedelta

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness import (
    FreshnessState,
    FreshnessStateChange,
    InternalFreshnessPolicy,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import instance_for_test
from dagster._time import get_current_timestamp
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

GET_FRESHNESS_STATUS_INFO = """
query GetFreshnessStatusInfo($assetKey: AssetKeyInput!) {
    assetNodes(assetKeys: [$assetKey]) {
        freshnessStatusInfo {
            freshnessStatus
            freshnessStatusMetadata {
                ... on AssetHealthFreshnessMeta {
                    lastMaterializedTimestamp
                }
            }
        }
    }
}
"""


@asset(
    freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )
)
def asset_with_freshness_with_warn_window():
    pass


@asset(freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=10)))
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
        assert instance.internal_asset_freshness_enabled()
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
            assert result.data["instance"]["freshnessEvaluationEnabled"] is True

            # starts off with no status
            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_STATUS_INFO,
                variables={"assetKey": asset_with_freshness.key.to_graphql_input()},
            )
            assert result.data["assetNodes"][0]["freshnessStatusInfo"] is not None
            assert (
                result.data["assetNodes"][0]["freshnessStatusInfo"]["freshnessStatus"] == "UNKNOWN"
            )

            # now it's healthy
            instance._report_runless_asset_event(  # noqa: SLF001
                asset_event=FreshnessStateChange(
                    key=asset_with_freshness.key,
                    previous_state=FreshnessState.UNKNOWN,
                    new_state=FreshnessState.PASS,
                    state_change_timestamp=get_current_timestamp(),
                )
            )

            # make sure it comes out as healthy
            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_STATUS_INFO,
                variables={"assetKey": asset_with_freshness.key.to_graphql_input()},
            )
            assert result.data["assetNodes"][0]["freshnessStatusInfo"] is not None
            assert (
                result.data["assetNodes"][0]["freshnessStatusInfo"]["freshnessStatus"] == "HEALTHY"
            )
