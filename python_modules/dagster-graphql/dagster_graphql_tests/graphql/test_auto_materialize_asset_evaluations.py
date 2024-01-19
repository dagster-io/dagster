import dagster._check as check
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY,
)
from dagster._serdes.serdes import serialize_value
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

AUTOMATION_POLICY_SENSORS_QUERY = """
query GetEvaluationsQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
        ... on AssetNode {
            currentAutoMaterializeEvaluationId
            targetingInstigators {
                ... on Schedule {
                    name
                }
                ... on Sensor {
                    name
                }
            }
        }
    }
}
"""

QUERY = """
query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    assetNodeOrError(assetKey: $assetKey) {
        ... on AssetNode {
            currentAutoMaterializeEvaluationId
        }
    }
    autoMaterializeAssetEvaluationsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
        ... on AutoMaterializeAssetEvaluationRecords {
            records {
                numRequested
                numSkipped
                numDiscarded
                rulesWithRuleEvaluations {
                    rule {
                        decisionType
                    }
                    ruleEvaluations {
                        partitionKeysOrError {
                            ... on PartitionKeys {
                                partitionKeys
                            }
                            ... on Error {
                                message
                            }
                        }
                        evaluationData {
                            ... on TextRuleEvaluationData {
                                text
                            }
                            ... on ParentMaterializedRuleEvaluationData {
                                updatedAssetKeys {
                                    path
                                }
                                willUpdateAssetKeys {
                                    path
                                }
                            }
                            ... on WaitingOnKeysRuleEvaluationData {
                                waitingOnAssetKeys {
                                    path
                                }
                            }
                        }
                    }
                }
                rules {
                    decisionType
                    description
                    className
                }
                assetKey {
                    path
                }
            }
        }
    }
}
"""

QUERY_FOR_EVALUATION_ID = """
query GetEvaluationsForEvaluationIdQuery($evaluationId: Int!) {
    autoMaterializeEvaluationsForEvaluationId(evaluationId: $evaluationId) {
        ... on AutoMaterializeAssetEvaluationRecords {
            records {
                numRequested
                numSkipped
                numDiscarded
                rulesWithRuleEvaluations {
                    rule {
                        decisionType
                    }
                    ruleEvaluations {
                        partitionKeysOrError {
                            ... on PartitionKeys {
                                partitionKeys
                            }
                            ... on Error {
                                message
                            }
                        }
                        evaluationData {
                            ... on TextRuleEvaluationData {
                                text
                            }
                            ... on ParentMaterializedRuleEvaluationData {
                                updatedAssetKeys {
                                    path
                                }
                                willUpdateAssetKeys {
                                    path
                                }
                            }
                            ... on WaitingOnKeysRuleEvaluationData {
                                waitingOnAssetKeys {
                                    path
                                }
                            }
                        }
                    }
                }
                rules {
                    decisionType
                    description
                    className
                }
                assetKey {
                    path
                }
            }
        }
    }
}
"""


class TestAutoMaterializeAssetEvaluations(ExecutingGraphQLContextTestMatrix):
    def test_get_historic_rules(self, graphql_context: WorkspaceRequestContext):
        evaluation1 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_one"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        evaluation2 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_two"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10, asset_evaluations=[evaluation1, evaluation2]
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_one"]}, "limit": 10, "cursor": None},
        )
        expected_rules = sorted(
            [
                {
                    "className": rs.description,
                    "decisionType": rs.decision_type.value,
                    "description": rs.description,
                }
                for rs in AutoMaterializePolicy.eager().rule_snapshots
            ],
            key=lambda x: x["className"],
        )

        assert len(results.data["autoMaterializeAssetEvaluationsOrError"]["records"]) == 1
        assert (
            results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["rules"]
            == expected_rules
        )
        assert results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["assetKey"] == {
            "path": ["asset_one"]
        }

        results_asset_two = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert len(results_asset_two.data["autoMaterializeAssetEvaluationsOrError"]["records"]) == 1
        assert (
            len(
                results_asset_two.data["autoMaterializeAssetEvaluationsOrError"]["records"][0][
                    "rules"
                ]
            )
            == 1
        )

        results_by_evaluation_id = execute_dagster_graphql(
            graphql_context,
            QUERY_FOR_EVALUATION_ID,
            variables={"evaluationId": 10},
        )

        records = results_by_evaluation_id.data["autoMaterializeEvaluationsForEvaluationId"][
            "records"
        ]

        assert len(records) == 2

        # record from both previous queries are contained here
        assert any(
            record == results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]
            for record in records
        )

        assert any(
            record == results_asset_two.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]
            for record in records
        )

        results_by_empty_evaluation_id = execute_dagster_graphql(
            graphql_context,
            QUERY_FOR_EVALUATION_ID,
            variables={"evaluationId": 12345},
        )
        assert (
            len(
                results_by_empty_evaluation_id.data["autoMaterializeEvaluationsForEvaluationId"][
                    "records"
                ]
            )
            == 0
        )

    def test_get_required_but_nonexistent_parent_evaluation(
        self, graphql_context: WorkspaceRequestContext
    ):
        evaluation = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["upstream_static_partitioned_asset"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 1, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["blah"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}}, {"__class__": "SerializedPartitionsSubset", "serialized_partitions_def_class_name": "StaticPartitionsDefinition", "serialized_partitions_def_unique_id": "7c2047f8b02e90a69136c1a657bd99ad80b433a2", "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            StaticPartitionsDefinition(["a", "b", "c", "d", "e", "f"]),
        )
        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[evaluation],
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "limit": 10,
                "cursor": None,
            },
        )

        expected_rules = sorted(
            [
                {
                    "className": rs.description,
                    "decisionType": rs.decision_type.value,
                    "description": rs.description,
                }
                for rs in AutoMaterializePolicy.eager().rule_snapshots
            ],
            key=lambda x: x["className"],
        )

        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "numRequested": 0,
                        "numSkipped": 1,
                        "numDiscarded": 0,
                        "rulesWithRuleEvaluations": [
                            {
                                "rule": {"decisionType": "SKIP"},
                                "ruleEvaluations": [
                                    {
                                        "evaluationData": {
                                            "waitingOnAssetKeys": [{"path": ["blah"]}],
                                        },
                                        "partitionKeysOrError": {
                                            "partitionKeys": ["a"],
                                        },
                                    }
                                ],
                            },
                        ],
                        "rules": expected_rules,
                        "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                    }
                ],
            },
        }

    def test_get_evaluations(self, graphql_context: WorkspaceRequestContext):
        evaluation1 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_one"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        evaluation2 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_two"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}}, null]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        evaluation3 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_three"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 1, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_two"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}}, null]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        evaluation4 = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_four"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "ParentUpdatedRuleEvaluationData", "updated_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_two"]}]}, "will_update_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_three"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}}, null]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            None,
        )
        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["foo"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "autoMaterializeAssetEvaluationsOrError": {"records": []},
            "assetNodeOrError": {"currentAutoMaterializeEvaluationId": None},
        }

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10, asset_evaluations=[evaluation1, evaluation2, evaluation3, evaluation4]
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_one"]}, "limit": 10, "cursor": None},
        )
        expected_rules = sorted(
            [
                {
                    "className": rs.description,
                    "decisionType": rs.decision_type.value,
                    "description": rs.description,
                }
                for rs in AutoMaterializePolicy.eager().rule_snapshots
            ],
            key=lambda x: x["className"],
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "assetKey": {"path": ["asset_one"]},
                        "numRequested": 0,
                        "numSkipped": 0,
                        "numDiscarded": 0,
                        "rules": expected_rules,
                        "rulesWithRuleEvaluations": [],
                    }
                ],
            },
        }

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "assetKey": {"path": ["asset_two"]},
                        "numRequested": 1,
                        "numSkipped": 0,
                        "numDiscarded": 0,
                        "rules": expected_rules,
                        "rulesWithRuleEvaluations": [
                            {
                                "rule": {"decisionType": "MATERIALIZE"},
                                "ruleEvaluations": [
                                    {
                                        "evaluationData": None,
                                        "partitionKeysOrError": None,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_three"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {},
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "assetKey": {"path": ["asset_three"]},
                        "numRequested": 0,
                        "numSkipped": 1,
                        "numDiscarded": 0,
                        "rules": expected_rules,
                        "rulesWithRuleEvaluations": [
                            {
                                "rule": {"decisionType": "SKIP"},
                                "ruleEvaluations": [
                                    {
                                        "evaluationData": {
                                            "waitingOnAssetKeys": [{"path": ["asset_two"]}],
                                        },
                                        "partitionKeysOrError": None,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_four"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {},
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "assetKey": {"path": ["asset_four"]},
                        "numRequested": 1,
                        "numSkipped": 0,
                        "numDiscarded": 0,
                        "rules": expected_rules,
                        "rulesWithRuleEvaluations": [
                            {
                                "rule": {"decisionType": "MATERIALIZE"},
                                "ruleEvaluations": [
                                    {
                                        "evaluationData": {
                                            "updatedAssetKeys": [{"path": ["asset_two"]}],
                                            "willUpdateAssetKeys": [{"path": ["asset_three"]}],
                                        },
                                        "partitionKeysOrError": None,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }

    def test_get_evaluations_with_partitions(self, graphql_context: WorkspaceRequestContext):
        evaluation = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["upstream_static_partitioned_asset"]}, "num_discarded": 0, "num_requested": 2, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}}, {"__class__": "SerializedPartitionsSubset", "serialized_partitions_def_class_name": "StaticPartitionsDefinition", "serialized_partitions_def_unique_id": "7c2047f8b02e90a69136c1a657bd99ad80b433a2", "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"a\\", \\"b\\"]}"}]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}',
            StaticPartitionsDefinition(["a", "b"]),
        )
        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "limit": 10,
                "cursor": None,
            },
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {"records": []},
        }

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(evaluation_id=10, asset_evaluations=[evaluation])

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "limit": 10,
                "cursor": None,
            },
        )

        assert len(results.data["autoMaterializeAssetEvaluationsOrError"]["records"]) == 1
        assert (
            (results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["numRequested"])
            == 2
        )
        assert (
            (results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["numSkipped"])
            == 0
        )
        assert (
            (results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["numDiscarded"])
            == 0
        )
        assert (
            (
                results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0][
                    "rulesWithRuleEvaluations"
                ][0]["rule"]["decisionType"]
            )
            == "MATERIALIZE"
        )
        assert set(
            results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0][
                "rulesWithRuleEvaluations"
            ][0]["ruleEvaluations"][0]["partitionKeysOrError"]["partitionKeys"]
        ) == {"a", "b"}

    def _test_current_evaluation_id(self, graphql_context: WorkspaceRequestContext):
        graphql_context.instance.daemon_cursor_storage.set_cursor_values(
            {_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(AssetDaemonCursor.empty(0))}
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": 0,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [],
            },
        }

        graphql_context.instance.daemon_cursor_storage.set_cursor_values(
            {
                _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: (
                    serialize_value(AssetDaemonCursor.empty(0).with_updates(0, 1.0, [], []))
                )
            }
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_two"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": 42,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [],
            },
        }
