import time

from dagster import AssetKey, DagsterEvent, DagsterEventType
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.event_api import EventLogRecord
from dagster._core.events import StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.test_utils import create_run_for_test
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
                assetKey {
                    path
                }
                description
                severity
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

GET_ASSET_CHECK_HISTORY_WITH_ID = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String) {
    assetChecksOrError(assetKey: $assetKey, checkName: $checkName) {
        ... on AssetChecks {
            checks {
                name
                executions(limit: 10) {
                    id
                    status
                }
            }
        }
    }
}
"""

GET_LOGS_FOR_RUN = """
query GetLogsForRun($runId: ID!) {
  logsForRun(runId: $runId) {
    __typename
    ... on EventConnection {
      events {
        __typename
      }
    }
  }
}
"""

GET_LATEST_EXECUTION = """
query GetLatestExecution($assetKey: AssetKeyInput!) {
    assetChecksOrError(assetKey: $assetKey) {
        ... on AssetChecks {
            checks {
                name
                executionForLatestMaterialization {
                    runId
                    status
                }
            }
        }
    }
}
"""


def _planned_event(run_id: str, planned: AssetCheckEvaluationPlanned) -> EventLogEntry:
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
            "nonce",
            event_specific_data=planned,
        ),
    )


def _evaluation_event(
    run_id: str, evaluation: AssetCheckEvaluation, timestamp=None
) -> EventLogEntry:
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp or time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_CHECK_EVALUATION.value,
            "nonce",
            event_specific_data=evaluation,
        ),
    )


def _materialization_event(run_id: str, asset_key: AssetKey) -> EventLogEntry:
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_MATERIALIZATION.value,
            "nonce",
            event_specific_data=StepMaterializationData(
                materialization=AssetMaterialization(asset_key=asset_key), asset_lineage=[]
            ),
        ),
    )


class TestAssetChecks(ExecutingGraphQLContextTestMatrix):
    def test_asset_check_definitions(self, graphql_context: WorkspaceRequestContext):
        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_CHECKS, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "assetKey": {
                            "path": ["asset_1"],
                        },
                        "description": "asset_1 check",
                        "severity": "ERROR",
                    }
                ]
            }
        }

    def test_asset_check_executions_with_id(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        run = create_run_for_test(graphql_context.instance)

        graphql_context.instance.event_log_storage.store_event(
            _planned_event(
                run.run_id,
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY_WITH_ID,
            variables={"assetKey": {"path": ["asset_1"]}, "checkName": "my_check"},
        )
        assert res.data
        assert res.data["assetChecksOrError"]["checks"][0]["executions"][0]["id"]
        assert (
            res.data["assetChecksOrError"]["checks"][0]["executions"][0]["status"] == "IN_PROGRESS"
        )

    def test_asset_check_executions(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        create_run_for_test(graphql_context.instance, run_id="foo")

        graphql_context.instance.event_log_storage.store_event(
            _planned_event(
                "foo",
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
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
                                "status": "IN_PROGRESS",
                                "evaluation": None,
                            }
                        ],
                    }
                ]
            }
        }

        evaluation_timestamp = time.time()

        graphql_context.instance.event_log_storage.store_event(
            _evaluation_event(
                "foo",
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    success=True,
                    metadata={"foo": MetadataValue.text("bar")},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=42, run_id="bizbuz", timestamp=3.3
                    ),
                ),
                timestamp=evaluation_timestamp,
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
                                "status": "SUCCEEDED",
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

    def test_asset_check_events(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        create_run_for_test(graphql_context.instance, run_id="foo")

        graphql_context.instance.event_log_storage.store_event(
            _planned_event(
                "foo",
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )
        graphql_context.instance.event_log_storage.store_event(
            _evaluation_event(
                "foo",
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    success=True,
                    metadata={"foo": MetadataValue.text("bar")},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=42, run_id="bizbuz", timestamp=3.3
                    ),
                ),
            )
        )

        res = execute_dagster_graphql(graphql_context, GET_LOGS_FOR_RUN, variables={"runId": "foo"})
        assert res.data == {
            "logsForRun": {
                "__typename": "EventConnection",
                "events": [
                    {
                        "__typename": "AssetCheckEvaluationPlannedEvent",
                    },
                    {
                        "__typename": "AssetCheckEvaluationEvent",
                    },
                ],
            }
        }

    def test_asset_check_failure(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        run = create_run_for_test(graphql_context.instance)

        graphql_context.instance.event_log_storage.store_event(
            _planned_event(
                run.run_id,
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
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
                                "runId": run.run_id,
                                "status": "IN_PROGRESS",
                                "evaluation": None,
                            }
                        ],
                    }
                ]
            }
        }

        graphql_context.instance.report_run_failed(run)

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
                            {"runId": run.run_id, "status": "EXECUTION_FAILED", "evaluation": None}
                        ],
                    }
                ],
            }
        }

    def test_latest_execution(self, graphql_context: WorkspaceRequestContext):
        instance = graphql_context.instance
        instance.wipe()

        def new_materialization() -> EventLogRecord:
            """Stores a materialization in a new run, and asserts that latest execustion is null."""
            run = create_run_for_test(instance)
            instance.event_log_storage.store_event(
                _materialization_event(run.run_id, AssetKey(["asset_1"]))
            )
            res = execute_dagster_graphql(
                graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
            )
            assert res.data == {
                "assetChecksOrError": {
                    "checks": [{"name": "my_check", "executionForLatestMaterialization": None}],
                }
            }, "new materialization should clear latest execution"
            return instance.get_records_for_run(run.run_id).records[0]

        # no materialization, surface latest execution
        run = create_run_for_test(instance)
        instance.event_log_storage.store_event(
            _planned_event(
                run.run_id,
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executionForLatestMaterialization": {
                            "runId": run.run_id,
                            "status": "IN_PROGRESS",
                        },
                    }
                ]
            }
        }
        instance.report_run_failed(run)
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executionForLatestMaterialization": {
                            "runId": run.run_id,
                            "status": "EXECUTION_FAILED",
                        },
                    }
                ],
            }
        }

        materialization_record = new_materialization()

        # check run targets the materialization
        run = create_run_for_test(instance)
        instance.event_log_storage.store_event(
            _planned_event(
                run.run_id,
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executionForLatestMaterialization": {
                            "runId": run.run_id,
                            "status": "IN_PROGRESS",
                        },
                    }
                ],
            }
        }
        instance.event_log_storage.store_event(
            _evaluation_event(
                run.run_id,
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    success=True,
                    metadata={},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=materialization_record.storage_id,
                        run_id=materialization_record.event_log_entry.run_id,
                        timestamp=materialization_record.event_log_entry.timestamp,
                    ),
                ),
            )
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetChecksOrError": {
                "checks": [
                    {
                        "name": "my_check",
                        "executionForLatestMaterialization": {
                            "runId": run.run_id,
                            "status": "SUCCEEDED",
                        },
                    }
                ],
            }
        }

        new_materialization()
