import dagster._check as check
from dagster import AssetKey, StaticPartitionsDefinition
from dagster._core.definitions.asset_reconciliation_sensor import (
    AutoMaterializeAssetEvaluation,
)
from dagster._core.definitions.auto_materialize_condition import MissingAutoMaterializeCondition
from dagster._core.definitions.partition import SerializedPartitionsSubset
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

QUERY = """
query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    autoMaterializeAssetEvaluations(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
        numRequested
        numSkipped
        numDiscarded
        conditions {
            __typename
            ... on AutoMaterializeConditionWithDecisionType {
                decisionType
            }
        }
    }
}
"""


class TestAutoMaterializeAssetEvaluations(ExecutingGraphQLContextTestMatrix):
    def test_get_evaluations(self, graphql_context: WorkspaceRequestContext):
        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["foo"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {"autoMaterializeAssetEvaluations": []}

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutoMaterializeAssetEvaluation(
                    asset_key=AssetKey("asset_one"),
                    partition_subsets_by_condition=[],
                    num_requested=0,
                    num_skipped=0,
                    num_discarded=0,
                ),
                AutoMaterializeAssetEvaluation(
                    asset_key=AssetKey("asset_two"),
                    partition_subsets_by_condition=[(MissingAutoMaterializeCondition(), None)],
                    num_requested=1,
                    num_skipped=0,
                    num_discarded=0,
                ),
            ],
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_one"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "autoMaterializeAssetEvaluations": [
                {"numRequested": 0, "numSkipped": 0, "numDiscarded": 0, "conditions": []}
            ]
        }

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "autoMaterializeAssetEvaluations": [
                {
                    "numRequested": 1,
                    "numSkipped": 0,
                    "numDiscarded": 0,
                    "conditions": [
                        {
                            "__typename": "MissingAutoMaterializeCondition",
                            "decisionType": "MATERIALIZE",
                        }
                    ],
                }
            ]
        }

    def test_get_evaluations_with_partitions(self, graphql_context: WorkspaceRequestContext):
        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["foo"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {"autoMaterializeAssetEvaluations": []}

        partitions_def = StaticPartitionsDefinition(["a", "b"])

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutoMaterializeAssetEvaluation(
                    asset_key=AssetKey("asset_two"),
                    partition_subsets_by_condition=[
                        (
                            MissingAutoMaterializeCondition(),
                            SerializedPartitionsSubset.from_subset(
                                partitions_def.empty_subset().with_partition_keys("a"),
                                partitions_def,
                                None,  # type: ignore
                            ),
                        )
                    ],
                    num_requested=1,
                    num_skipped=0,
                    num_discarded=0,
                ),
            ],
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "autoMaterializeAssetEvaluations": [
                {
                    "numRequested": 1,
                    "numSkipped": 0,
                    "numDiscarded": 0,
                    "conditions": [
                        {
                            "__typename": "MissingAutoMaterializeCondition",
                            "decisionType": "MATERIALIZE",
                        }
                    ],
                }
            ]
        }
