import time

from dagster import DagsterEvent, DagsterEventType
from dagster._core.definitions.data_time import DATA_TIME_METADATA_KEY
from dagster._core.definitions.events import AssetObservation
from dagster._core.events import AssetObservationData
from dagster._core.events.log import EventLogEntry
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
)

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

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

BaseTestSuite = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_multi_location()]
)


class TestAssetFreshness(BaseTestSuite):
    def test_source_asset_freshness_policy(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_FRESHNESS_INFO,
            variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
        )
        assert result.data
        assert result.data["assetNodes"][0]["freshnessPolicy"]

    def test_source_asset_freshness_info(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_FRESHNESS_INFO,
            variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
        )
        assert result.data
        assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] is None

        graphql_context.instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id="foo",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_OBSERVATION.value,
                    "nonce",
                    event_specific_data=AssetObservationData(
                        AssetObservation(
                            asset_key="source_asset_with_freshness",
                            metadata={DATA_TIME_METADATA_KEY: time.time() - 60 * 60},
                        )
                    ),
                ),
            )
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_FRESHNESS_INFO,
            variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
        )
        assert result.data
        assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] >= 30

        graphql_context.instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id="foo",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_OBSERVATION.value,
                    "nonce",
                    event_specific_data=AssetObservationData(
                        AssetObservation(
                            asset_key="source_asset_with_freshness",
                            metadata={DATA_TIME_METADATA_KEY: time.time()},
                        )
                    ),
                ),
            )
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_FRESHNESS_INFO,
            variables={"assetKeys": [{"path": ["source_asset_with_freshness"]}]},
        )
        assert result.data
        assert result.data["assetNodes"][0]["freshnessInfo"]["currentMinutesLate"] == 0
