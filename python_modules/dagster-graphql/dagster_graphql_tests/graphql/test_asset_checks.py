import time

from dagster import AssetKey, DagsterEvent, DagsterEventType
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.event_api import EventLogRecord
from dagster._core.events import StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.test_utils import create_run_for_test, poll_for_finished_run
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import ERROR_FRAGMENT
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_job_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_ASSET_CHECK_DETAILS_QUERY = """
query AssetNodeChecksLimitQuery($assetKeys: [AssetKeyInput!], $limit: Int) {
    assetNodes(assetKeys: $assetKeys) {
        assetKey {
            path
        }
        assetChecksOrError(limit: $limit) {
            ... on AssetChecks {
                checks {
                    name
                    description
                    canExecuteIndividually
                }
            }
        }
    }
}
"""

GET_ASSET_CHECK_NAMES_QUERY = """
query AssetNodeChecksLimitQuery($assetKeys: [AssetKeyInput!], $limit: Int, $pipelineSelector: PipelineSelector) {
    assetNodes(assetKeys: $assetKeys, pipeline: $pipelineSelector) {
        assetKey {
            path
        }
        assetChecksOrError(limit: $limit, pipeline: $pipelineSelector) {
            ... on AssetChecks {
                checks {
                    name
                }
            }
        }
    }
}
"""

GET_ASSET_CHECK_HISTORY_WITH_ID = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String!, $limit: Int!, $cursor: String) {
    assetCheckExecutions(assetKey: $assetKey, checkName: $checkName, limit: $limit, cursor: $cursor) {
        id
        status
        runId
    }
}
"""


GET_ASSET_CHECK_HISTORY = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String!) {
    assetCheckExecutions(assetKey: $assetKey, checkName: $checkName, limit: 10) {
        runId
        status
        evaluation {
            severity
            timestamp
            targetMaterialization {
                storageId
                runId
                timestamp
            }
            metadataEntries {
                label
            }
            description
        }
    }
}
"""

GET_LATEST_EXECUTION = """
query GetLatestExecution($assetKey: AssetKeyInput!) {
    assetNodes(assetKeys: [$assetKey]) {
        assetChecksOrError {
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
}
"""

GET_ASSET_CHECK_HISTORY_WITH_STEP_KEY = """
query GetAssetChecksQuery($assetKey: AssetKeyInput!, $checkName: String!) {
    assetCheckExecutions(assetKey: $assetKey, checkName: $checkName, limit: 10) {
        runId
        status
        stepKey
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


LAUNCH_PIPELINE_EXECUTION_MUTATION = (
    ERROR_FRAGMENT
    + """
mutation($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    __typename

    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on LaunchRunSuccess {
      run {
        runId
        pipeline {
          name
        }
        tags {
          key
          value
        }
        status
        runConfigYaml
        mode
        resolvedOpSelection
      }
    }
    ... on ConflictingExecutionParamsError {
      message
    }
    ... on PresetNotFoundError {
      preset
      message
    }
    ... on RunConfigValidationInvalid {
      pipelineName
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      ...errorFragment
    }
    ... on InvalidSubsetError {
        message
    }
  }
}
"""
)

RUN_QUERY = """
query RunQuery($runId: ID!) {
  runOrError(runId: $runId) {
    __typename
    ... on Run {
        assetSelection {
            path
        }
        assetCheckSelection {
            assetKey {
                path
            }
            name
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
            graphql_context,
            GET_ASSET_CHECK_DETAILS_QUERY,
            variables={"assetKeys": [{"path": ["asset_1"]}]},
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetKey": {"path": ["asset_1"]},
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "description": "asset_1 check",
                                "canExecuteIndividually": "CAN_EXECUTE",
                            }
                        ]
                    },
                }
            ]
        }

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_DETAILS_QUERY,
            variables={"assetKeys": {"path": ["check_in_op_asset"]}},
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetKey": {"path": ["check_in_op_asset"]},
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "description": None,
                                "canExecuteIndividually": "REQUIRES_MATERIALIZATION",
                            }
                        ]
                    },
                }
            ]
        }

    def test_asset_check_asset_node_limit(self, graphql_context: WorkspaceRequestContext):
        res = execute_dagster_graphql(graphql_context, GET_ASSET_CHECK_NAMES_QUERY)
        with_checks = [
            node for node in res.data["assetNodes"] if node["assetChecksOrError"] != {"checks": []}
        ]
        assert with_checks == [
            {
                "assetKey": {"path": ["asset_1"]},
                "assetChecksOrError": {"checks": [{"name": "my_check"}]},
            },
            {
                "assetKey": {"path": ["check_in_op_asset"]},
                "assetChecksOrError": {"checks": [{"name": "my_check"}]},
            },
            {
                "assetKey": {"path": ["one"]},
                "assetChecksOrError": {
                    "checks": [{"name": "my_check"}, {"name": "my_other_check"}]
                },
            },
        ]

        res = execute_dagster_graphql(
            graphql_context, GET_ASSET_CHECK_NAMES_QUERY, variables={"limit": 1}
        )
        with_checks = [
            node for node in res.data["assetNodes"] if node["assetChecksOrError"] != {"checks": []}
        ]
        assert with_checks == [
            {
                "assetKey": {"path": ["asset_1"]},
                "assetChecksOrError": {"checks": [{"name": "my_check"}]},
            },
            {
                "assetKey": {"path": ["check_in_op_asset"]},
                "assetChecksOrError": {"checks": [{"name": "my_check"}]},
            },
            {
                "assetKey": {"path": ["one"]},
                "assetChecksOrError": {"checks": [{"name": "my_check"}]},
            },
        ]

    def test_asset_check_asset_node_job_selection(self, graphql_context: WorkspaceRequestContext):
        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_NAMES_QUERY,
            variables={
                "pipelineSelector": infer_job_selector(
                    graphql_context, "fail_partition_materialization_job"
                )
            },
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetKey": {"path": ["fail_partition_materialization"]},
                    "assetChecksOrError": {"checks": []},
                }
            ]
        }

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_NAMES_QUERY,
            variables={"pipelineSelector": infer_job_selector(graphql_context, "asset_check_job")},
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetChecksOrError": {"checks": [{"name": "my_check"}]},
                    "assetKey": {"path": ["asset_1"]},
                },
                {
                    "assetChecksOrError": {"checks": [{"name": "my_check"}]},
                    "assetKey": {"path": ["check_in_op_asset"]},
                },
            ]
        }

    def test_asset_check_execution_cursoring(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        run_ids = [create_run_for_test(graphql_context.instance).run_id for _ in range(10)]
        for run_id in run_ids:
            graphql_context.instance.event_log_storage.store_event(
                _planned_event(
                    run_id,
                    AssetCheckEvaluationPlanned(
                        asset_key=AssetKey(["asset_1"]), check_name="my_check"
                    ),
                )
            )

        expected_limit = 6
        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY_WITH_ID,
            variables={
                "assetKey": {"path": ["asset_1"]},
                "checkName": "my_check",
                "limit": expected_limit,
            },
        )
        assert res.data
        expected_run_ids = list(reversed(run_ids))[:expected_limit]
        for expected_run_id, execution in zip(expected_run_ids, res.data["assetCheckExecutions"]):
            assert execution["runId"] == expected_run_id

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY_WITH_ID,
            variables={
                "assetKey": {"path": ["asset_1"]},
                "checkName": "my_check",
                "limit": expected_limit,
                "cursor": res.data["assetCheckExecutions"][-1]["id"],
            },
        )
        assert res.data
        expected_run_ids = list(reversed(run_ids))[expected_limit:]
        for expected_run_id, execution in zip(expected_run_ids, res.data["assetCheckExecutions"]):
            assert execution["runId"] == expected_run_id

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
            "assetCheckExecutions": [
                {
                    "runId": "foo",
                    "status": "IN_PROGRESS",
                    "evaluation": None,
                }
            ],
        }

        evaluation_timestamp = time.time()

        graphql_context.instance.event_log_storage.store_event(
            _evaluation_event(
                "foo",
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    passed=True,
                    metadata={"foo": MetadataValue.text("bar")},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=42, run_id="bizbuz", timestamp=3.3
                    ),
                    severity=AssetCheckSeverity.ERROR,
                    description="evaluation description",
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
            "assetCheckExecutions": [
                {
                    "runId": "foo",
                    "status": "SUCCEEDED",
                    "evaluation": {
                        "timestamp": evaluation_timestamp,
                        "severity": "ERROR",
                        "targetMaterialization": {
                            "storageId": 42,
                            "runId": "bizbuz",
                            "timestamp": 3.3,
                        },
                        "metadataEntries": [
                            {"label": "foo"},
                        ],
                        "description": "evaluation description",
                    },
                }
            ],
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
                    passed=True,
                    metadata={"foo": MetadataValue.text("bar")},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=42, run_id="bizbuz", timestamp=3.3
                    ),
                    severity=AssetCheckSeverity.ERROR,
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
            "assetCheckExecutions": [
                {
                    "runId": run.run_id,
                    "status": "IN_PROGRESS",
                    "evaluation": None,
                }
            ],
        }

        graphql_context.instance.report_run_failed(run)

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY,
            variables={"assetKey": {"path": ["asset_1"]}, "checkName": "my_check"},
        )
        assert res.data == {
            "assetCheckExecutions": [
                {"runId": run.run_id, "status": "EXECUTION_FAILED", "evaluation": None}
            ],
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
                "assetNodes": [
                    {
                        "assetChecksOrError": {
                            "checks": [
                                {"name": "my_check", "executionForLatestMaterialization": None}
                            ]
                        }
                    }
                ]
            }, "new materialization should clear latest execution"
            records = instance.get_asset_records([AssetKey(["asset_1"])])
            assert records
            assert records[0].asset_entry.last_materialization_record
            return records[0].asset_entry.last_materialization_record

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
            "assetNodes": [
                {
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
            ]
        }
        instance.report_run_failed(run)
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "executionForLatestMaterialization": {
                                    "runId": run.run_id,
                                    "status": "EXECUTION_FAILED",
                                },
                            }
                        ]
                    },
                }
            ]
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
            "assetNodes": [
                {
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
                    },
                }
            ]
        }
        instance.event_log_storage.store_event(
            _evaluation_event(
                run.run_id,
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    passed=True,
                    metadata={},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=materialization_record.storage_id,
                        run_id=materialization_record.event_log_entry.run_id,
                        timestamp=materialization_record.event_log_entry.timestamp,
                    ),
                    severity=AssetCheckSeverity.ERROR,
                ),
            )
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "executionForLatestMaterialization": {
                                    "runId": run.run_id,
                                    "status": "SUCCEEDED",
                                },
                            }
                        ]
                    },
                }
            ]
        }

        materialization_record = new_materialization()

        # run the checks, then materialize. The checks still apply because they're in the same run
        run = create_run_for_test(instance)
        instance.event_log_storage.store_event(
            _planned_event(
                run.run_id,
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )
        instance.event_log_storage.store_event(
            _evaluation_event(
                run.run_id,
                AssetCheckEvaluation(
                    asset_key=AssetKey(["asset_1"]),
                    check_name="my_check",
                    passed=True,
                    metadata={},
                    target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                        storage_id=materialization_record.storage_id,
                        run_id=materialization_record.event_log_entry.run_id,
                        timestamp=materialization_record.event_log_entry.timestamp,
                    ),
                    severity=AssetCheckSeverity.ERROR,
                ),
            )
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "executionForLatestMaterialization": {
                                    "runId": run.run_id,
                                    "status": "SUCCEEDED",
                                },
                            }
                        ]
                    },
                }
            ]
        }
        instance.event_log_storage.store_event(
            _materialization_event(run.run_id, AssetKey(["asset_1"]))
        )
        res = execute_dagster_graphql(
            graphql_context, GET_LATEST_EXECUTION, variables={"assetKey": {"path": ["asset_1"]}}
        )
        assert res.data == {
            "assetNodes": [
                {
                    "assetChecksOrError": {
                        "checks": [
                            {
                                "name": "my_check",
                                "executionForLatestMaterialization": {
                                    "runId": run.run_id,
                                    "status": "SUCCEEDED",
                                },
                            }
                        ]
                    },
                }
            ]
        }

        new_materialization()

    def test_launch_subset_with_only_check(self, graphql_context: WorkspaceRequestContext):
        # materialize the asset and run the check first
        selector = infer_job_selector(
            graphql_context,
            "asset_check_job",
            asset_selection=[{"path": ["asset_1"]}],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        result = execute_dagster_graphql(graphql_context, RUN_QUERY, variables={"runId": run_id})
        assert result.data == {
            "runOrError": {
                "__typename": "Run",
                "assetSelection": [{"path": ["asset_1"]}],
                "assetCheckSelection": None,
            }
        }

        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        checks = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(checks) == 1

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 1

        selector = infer_job_selector(
            graphql_context,
            "asset_check_job",
            asset_selection=[],
            asset_check_selection=[{"assetKey": {"path": ["asset_1"]}, "name": "my_check"}],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        result = execute_dagster_graphql(graphql_context, RUN_QUERY, variables={"runId": run_id})
        assert result.data == {
            "runOrError": {
                "__typename": "Run",
                "assetSelection": None,
                "assetCheckSelection": [
                    {"assetKey": {"path": ["asset_1"]}, "name": "my_check"},
                ],
            }
        }

        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 1

        for log in logs:
            if log.dagster_event:
                assert log.dagster_event.event_type != DagsterEventType.ASSET_MATERIALIZATION.value

    def test_launch_subset_asset_and_included_check(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "asset_check_job",
            asset_selection=[{"path": ["asset_1"]}],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        result = execute_dagster_graphql(graphql_context, RUN_QUERY, variables={"runId": run_id})
        assert result.data == {
            "runOrError": {
                "__typename": "Run",
                "assetSelection": [{"path": ["asset_1"]}],
                "assetCheckSelection": None,
            }
        }

        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 1

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 1

    def test_check_subset_error(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "asset_check_job",
            asset_check_selection=[
                {"assetKey": {"path": ["asset_1"]}, "name": "non-existent-check"}
            ],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "InvalidSubsetError"
        assert (
            result.data["launchPipelineExecution"]["message"]
            == "dagster._core.errors.DagsterInvalidSubsetError: AssetCheckKey(s)"
            " ['asset_1:non-existent-check'] were selected, but no definitions supply these keys."
            " Make sure all keys are spelled correctly, and all definitions are correctly added to"
            " the `Definitions`.\n"
        )

    def test_launch_subset_asset_no_check(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "asset_check_job",
            asset_selection=[{"path": ["asset_1"]}],
            asset_check_selection=[],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        for log in logs:
            if log.dagster_event:
                assert log.dagster_event.event_type != DagsterEventType.ASSET_CHECK_EVALUATION.value

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 1

    def test_multi_asset(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 2

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 2

    def test_multi_asset_without_check(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
            asset_selection=[{"path": ["one"]}],
            asset_check_selection=[],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 0

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 1

        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
            asset_selection=[{"path": ["two"]}],
            asset_check_selection=[],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 0

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 1

        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
            asset_selection=[{"path": ["one"]}, {"path": ["two"]}],
            asset_check_selection=[],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 0

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 2

    def test_multi_asset_only_check(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
            asset_selection=[],
            asset_check_selection=[
                {"assetKey": {"path": ["one"]}, "name": "my_check"},
            ],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id, timeout=10000000000)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        check_evaluations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        assert len(check_evaluations) == 1

        materializations = [
            log
            for log in logs
            if log.dagster_event
            and log.dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ]
        assert len(materializations) == 0

    def test_step_key(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(
            graphql_context,
            "checked_multi_asset_job",
            asset_selection=[],
            asset_check_selection=[
                {"assetKey": {"path": ["one"]}, "name": "my_check"},
            ],
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "stepKeys": None,
                }
            },
        )
        print(result.data)  # noqa: T201
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        run = poll_for_finished_run(graphql_context.instance, run_id, timeout=10000000000)

        logs = graphql_context.instance.all_logs(run_id)
        print(logs)  # noqa: T201
        assert run.is_success

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY_WITH_STEP_KEY,
            variables={"assetKey": {"path": ["one"]}, "checkName": "my_check", "limit": 10},
        )
        print(result.data)  # noqa: T201
        assert result.data == {
            "assetCheckExecutions": [
                {
                    "runId": run_id,
                    "status": "SUCCEEDED",
                    "stepKey": "subsettable_checked_multi_asset",
                }
            ],
        }

    def test_deleted_run(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.wipe()

        run = create_run_for_test(graphql_context.instance, run_id="foo")

        graphql_context.instance.event_log_storage.store_event(
            _planned_event(
                "foo",
                AssetCheckEvaluationPlanned(asset_key=AssetKey(["asset_1"]), check_name="my_check"),
            )
        )

        graphql_context.instance.delete_run(run.run_id)

        res = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_CHECK_HISTORY,
            variables={"assetKey": {"path": ["asset_1"]}, "checkName": "my_check"},
        )
        assert res.data == {
            "assetCheckExecutions": [
                {
                    "runId": "foo",
                    "status": "SKIPPED",
                    "evaluation": None,
                }
            ],
        }
