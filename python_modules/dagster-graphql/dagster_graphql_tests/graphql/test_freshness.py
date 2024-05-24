from datetime import datetime, timezone

from dagster import (
    Definitions,
    FreshnessPolicy,
    ObserveResult,
    RepositoryDefinition,
    observable_source_asset,
)
from dagster._core.definitions.data_time import DATA_TIME_METADATA_KEY
from dagster._core.definitions.observe import observe
from dagster._core.test_utils import instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

GET_FRESHNESS_INFO = """
    query AssetNodeQuery($assetKeys: [AssetKeyInput!]!) {
        assetNodes(assetKeys: $assetKeys) {
            id
            freshnessInfo {
                currentMinutesLate
                latestMaterializationMinutesLate
            }
            freshnessPolicy {
                cronSchedule
                maximumLagMinutes
            }
        }
    }
"""


@observable_source_asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=30))
def source_asset_with_freshness(context):
    return ObserveResult(metadata={DATA_TIME_METADATA_KEY: float(context.run.tags["data_time"])})


def get_repo() -> RepositoryDefinition:
    return Definitions(assets=[source_asset_with_freshness]).get_repository_def()


def test_source_asset_freshness_policy():
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as graphql_context:
            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_INFO,
                variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
            )
            assert result.data
            assert result.data["assetNodes"][0]["freshnessPolicy"]


def test_source_asset_freshness_info():
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as graphql_context:
            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_INFO,
                variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
            )
            assert result.data
            assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] is None

            observe(
                [source_asset_with_freshness],
                instance=instance,
                tags={"data_time": str(datetime.now(timezone.utc).timestamp() - 1000 * 60 * 35)},
            )

            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_INFO,
                variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
            )
            assert result.data
            assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] >= 30

            observe(
                [source_asset_with_freshness],
                instance=instance,
                tags={"data_time": str(datetime.now(timezone.utc).timestamp())},
            )

            result = execute_dagster_graphql(
                graphql_context,
                GET_FRESHNESS_INFO,
                variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
            )
            assert result.data
            assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] == 0
