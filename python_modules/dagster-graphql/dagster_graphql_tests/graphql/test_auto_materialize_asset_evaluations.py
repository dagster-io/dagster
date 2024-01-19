from typing import Sequence
from unittest.mock import PropertyMock, patch

import dagster._check as check
import pendulum
from dagster import AssetKey, RunRequest
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
)
from dagster._core.definitions.run_request import (
    InstigatorType,
)
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.host_representation.origin import (
    ExternalInstigatorOrigin,
)
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY,
    _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    asset_daemon_cursor_to_instigator_serialized_cursor,
)
from dagster._serdes import deserialize_value
from dagster._serdes.serdes import serialize_value
from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

TICKS_QUERY = """
query AssetDameonTicksQuery($dayRange: Int, $dayOffset: Int, $statuses: [InstigationTickStatus!], $limit: Int, $cursor: String, $beforeTimestamp: Float, $afterTimestamp: Float) {
    autoMaterializeTicks(dayRange: $dayRange, dayOffset: $dayOffset, statuses: $statuses, limit: $limit, cursor: $cursor, beforeTimestamp: $beforeTimestamp, afterTimestamp: $afterTimestamp) {
        id
        timestamp
        endTimestamp
        status
        requestedAssetKeys {
            path
        }
        requestedMaterializationsForAssets {
            assetKey {
                path
            }
            partitionKeys
        }
        requestedAssetMaterializationCount
        autoMaterializeAssetEvaluationId
    }
}
"""


def _create_tick(instance, status, timestamp, evaluation_id, run_requests=None, end_timestamp=None):
    return instance.create_tick(
        TickData(
            instigator_origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            instigator_name=_PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
            instigator_type=InstigatorType.AUTO_MATERIALIZE,
            status=status,
            timestamp=timestamp,
            end_timestamp=end_timestamp,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
            run_ids=[],
            auto_materialize_evaluation_id=evaluation_id,
            run_requests=run_requests,
        )
    )


class TestAutoMaterializeTicks(ExecutingGraphQLContextTestMatrix):
    def test_get_tick_range(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={"dayRange": None, "dayOffset": None},
        )
        assert len(result.data["autoMaterializeTicks"]) == 0

        now = pendulum.now("UTC")
        end_timestamp = now.timestamp() + 20

        success_1 = _create_tick(
            graphql_context.instance,
            TickStatus.SUCCESS,
            now.timestamp(),
            end_timestamp=end_timestamp,
            evaluation_id=3,
            run_requests=[
                RunRequest(asset_selection=[AssetKey("foo"), AssetKey("bar")], partition_key="abc"),
                RunRequest(asset_selection=[AssetKey("bar")], partition_key="def"),
                RunRequest(asset_selection=[AssetKey("baz")], partition_key=None),
            ],
        )

        success_2 = _create_tick(
            graphql_context.instance,
            TickStatus.SUCCESS,
            now.subtract(days=1, hours=1).timestamp(),
            evaluation_id=2,
        )

        _create_tick(
            graphql_context.instance,
            TickStatus.SKIPPED,
            now.subtract(days=2, hours=1).timestamp(),
            evaluation_id=1,
        )

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={"dayRange": None, "dayOffset": None},
        )
        assert len(result.data["autoMaterializeTicks"]) == 3

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={"dayRange": 1, "dayOffset": None},
        )
        assert len(result.data["autoMaterializeTicks"]) == 1
        tick = result.data["autoMaterializeTicks"][0]
        assert tick["endTimestamp"] == end_timestamp
        assert tick["autoMaterializeAssetEvaluationId"] == 3
        assert sorted(tick["requestedAssetKeys"], key=lambda x: x["path"][0]) == [
            {"path": ["bar"]},
            {"path": ["baz"]},
            {"path": ["foo"]},
        ]

        asset_materializations = tick["requestedMaterializationsForAssets"]
        by_asset_key = {
            AssetKey.from_coercible(mat["assetKey"]["path"]).to_user_string(): mat["partitionKeys"]
            for mat in asset_materializations
        }

        assert {key: sorted(val) for key, val in by_asset_key.items()} == {
            "foo": ["abc"],
            "bar": ["abc", "def"],
            "baz": [],
        }

        assert tick["requestedAssetMaterializationCount"] == 4

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={
                "beforeTimestamp": success_2.timestamp + 1,
                "afterTimestamp": success_2.timestamp - 1,
            },
        )
        assert len(result.data["autoMaterializeTicks"]) == 1
        tick = result.data["autoMaterializeTicks"][0]
        assert (
            tick["autoMaterializeAssetEvaluationId"]
            == success_2.tick_data.auto_materialize_evaluation_id
        )

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={"dayRange": None, "dayOffset": None, "statuses": ["SUCCESS"]},
        )
        assert len(result.data["autoMaterializeTicks"]) == 2

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={"dayRange": None, "dayOffset": None, "statuses": ["SUCCESS"], "limit": 1},
        )
        ticks = result.data["autoMaterializeTicks"]
        assert len(ticks) == 1
        assert ticks[0]["timestamp"] == success_1.timestamp
        assert (
            ticks[0]["autoMaterializeAssetEvaluationId"]
            == success_1.tick_data.auto_materialize_evaluation_id
        )

        cursor = ticks[0]["id"]

        result = execute_dagster_graphql(
            graphql_context,
            TICKS_QUERY,
            variables={
                "dayRange": None,
                "dayOffset": None,
                "statuses": ["SUCCESS"],
                "limit": 1,
                "cursor": cursor,
            },
        )
        ticks = result.data["autoMaterializeTicks"]
        assert len(ticks) == 1
        assert ticks[0]["timestamp"] == success_2.timestamp


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
    def test_automation_policy_sensor(self, graphql_context: WorkspaceRequestContext):
        sensor_origin = ExternalInstigatorOrigin(
            external_repository_origin=infer_repository(graphql_context).get_external_origin(),
            instigator_name="my_automation_policy_sensor",
        )

        check.not_none(graphql_context.instance.schedule_storage).add_instigator_state(
            InstigatorState(
                sensor_origin,
                InstigatorType.SENSOR,
                status=InstigatorStatus.RUNNING,
                instigator_data=SensorInstigatorData(
                    sensor_type=SensorType.AUTOMATION_POLICY,
                    cursor=asset_daemon_cursor_to_instigator_serialized_cursor(
                        AssetDaemonCursor.empty(12345)
                    ),
                ),
            )
        )

        results = execute_dagster_graphql(
            graphql_context,
            AUTOMATION_POLICY_SENSORS_QUERY,
            variables={
                "assetKey": {"path": ["fresh_diamond_bottom"]},
            },
        )
        assert not results.data["assetNodeOrError"]["currentAutoMaterializeEvaluationId"]

        with patch(
            "dagster._core.instance.DagsterInstance.auto_materialize_use_automation_policy_sensors",
            new_callable=PropertyMock,
        ) as mock_my_property:
            mock_my_property.return_value = True

            results = execute_dagster_graphql(
                graphql_context,
                AUTOMATION_POLICY_SENSORS_QUERY,
                variables={
                    "assetKey": {"path": ["fresh_diamond_bottom"]},
                },
            )

            assert any(
                instigator["name"] == "my_automation_policy_sensor"
                for instigator in results.data["assetNodeOrError"]["targetingInstigators"]
            )
            assert results.data["assetNodeOrError"]["currentAutoMaterializeEvaluationId"] == 12345

    def test_get_historic_rules(self, graphql_context: WorkspaceRequestContext):
        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=deserialize_value(
                '[{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_one"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": null, "run_ids": {"__set__": []}}, {"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_two"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}], "run_ids": {"__set__": []}}]',
                Sequence,
            ),
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_one"]}, "limit": 10, "cursor": None},
        )
        assert len(results.data["autoMaterializeAssetEvaluationsOrError"]["records"]) == 1
        assert results.data["autoMaterializeAssetEvaluationsOrError"]["records"][0]["rules"] == []
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
            == 0
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
        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=deserialize_value(
                '[{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["upstream_static_partitioned_asset"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 1, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["blah"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not exist"}}, {"__class__": "SerializedPartitionsSubset", "serialized_partitions_def_class_name": "StaticPartitionsDefinition", "serialized_partitions_def_unique_id": "7c2047f8b02e90a69136c1a657bd99ad80b433a2", "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]], "rule_snapshots": null, "run_ids": {"__set__": []}}]',
                Sequence,
            ),
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
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "numRequested": 0,
                        "numSkipped": 0,
                        "numDiscarded": 0,
                        "rulesWithRuleEvaluations": [],
                        "rules": [],
                        "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                    }
                ],
            },
        }

    def _test_get_evaluations(self, graphql_context: WorkspaceRequestContext):
        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["foo"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "autoMaterializeAssetEvaluationsOrError": {"records": []},
        }

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=deserialize_value(
                '[{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_one"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 0, "partition_subsets_by_condition": [], "rule_snapshots": null, "run_ids": {"__set__": []}}, {"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_two"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}}, null]], "rule_snapshots": null, "run_ids": {"__set__": []}}, {"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_three"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 1, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_two"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to date"}}, null]], "rule_snapshots": null, "run_ids": {"__set__": []}}, {"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["asset_four"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": "ParentUpdatedRuleEvaluationData", "updated_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_two"]}]}, "will_update_asset_keys": {"__frozenset__": [{"__class__": "AssetKey", "path": ["asset_three"]}]}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed since latest materialization"}}, null]], "rule_snapshots": null, "run_ids": {"__set__": []}}]',
                Sequence,
            ),
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["asset_one"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "numRequested": 0,
                        "numSkipped": 0,
                        "numDiscarded": 0,
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
                        "numRequested": 1,
                        "numSkipped": 0,
                        "numDiscarded": 0,
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
            "assetNodeOrError": {
                "currentAutoMaterializeEvaluationId": None,
            },
            "autoMaterializeAssetEvaluationsOrError": {
                "records": [
                    {
                        "numRequested": 1,
                        "numSkipped": 0,
                        "numDiscarded": 0,
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

    def _test_get_evaluations_with_partitions(self, graphql_context: WorkspaceRequestContext):
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
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=deserialize_value(
                '[{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", "path": ["upstream_static_partitioned_asset"]}, "num_discarded": 0, "num_requested": 2, "num_skipped": 0, "partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}}, {"__class__": "SerializedPartitionsSubset", "serialized_partitions_def_class_name": "StaticPartitionsDefinition", "serialized_partitions_def_unique_id": "7c2047f8b02e90a69136c1a657bd99ad80b433a2", "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"a\\", \\"b\\"]}"}]], "rule_snapshots": null, "run_ids": {"__set__": []}}]',
                Sequence,
            ),
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
