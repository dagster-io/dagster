import time

from dagster import AssetKey, DagsterEvent, DagsterEventType
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_ASSET_CHECKS = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String) {
    assetChecksOrError(assetKey: $assetKey, checkName: $checkName) {
        ... on AssetChecks {
            checks {
                name
                description
            }
        }
    }
}
"""

GET_ASSET_CHECK_HISTORY = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String) {
    assetChecksOrError(assetKey: $assetKey, checkName: $checkName) {
        ... on AssetChecks {
            checks {
                name
                executions(limit: 10) {
                    runId
                    status
                    evaluation {
                        timestamp
                        targetMaterialization {
                            storageId
                            runId
                            timestamp
                        }
                        metadataEntries {
                            label
                        }
                    }
                }
            }
        }
    }
}
"""


class TestAssetChecks(ExecutingGraphQLContextTestMatrix):
    def test_asset_checks(self, graphql_context: WorkspaceRequestContext, snapshot):
        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_CHECKS, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "description": "asset_1 check",
                    }
                ]
            }
        }

        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_CHECKS, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "description": "asset_1 check",
                    }
                ]
            }
        }

        graphql_context.instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="foo",
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=AssetKey(["asset_1"]), check_name="my_check"
                    ),
                ),
            )
        )

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY,
            variables={"assetKey": {"path": ["asset_1"]}, "checkName": "my_check"},
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executions": [
                            {
                                "runId": "foo",
                                "status": "PLANNED",
                                "evaluation": None,
                            }
                        ],
                    }
                ]
            }
        }

        evaluation_timestamp = time.time()

        graphql_context.instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id="foo",
                timestamp=evaluation_timestamp,
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluation(
                        asset_key=AssetKey(["asset_1"]),
                        check_name="my_check",
                        success=True,
                        metadata={"foo": MetadataValue.text("bar")},
                        target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                            storage_id=42, run_id="bizbuz", timestamp=3.3
                        ),
                    ),
                ),
            )
        )

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY,
            variables={"assetKey": {"path": ["asset_1"]}, "checkName": "my_check"},
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executions": [
                            {
                                "runId": "foo",
                                "status": "SUCCESS",
                                "evaluation": {
                                    "timestamp": evaluation_timestamp,
                                    "targetMaterialization": {
                                        "storageId": 42,
                                        "runId": "bizbuz",
                                        "timestamp": 3.3,
                                    },
                                    "metadataEntries": [
                                        {"label": "foo"},
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        }
