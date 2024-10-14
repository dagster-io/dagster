import random
from typing import Any, Mapping, Optional, Sequence
from unittest.mock import PropertyMock, patch

import dagster._check as check
from dagster import AssetKey, AutomationCondition, RunRequest, asset, evaluate_automation_conditions
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
    AutomationConditionEvaluationWithRunIds,
    AutomationConditionNodeSnapshot,
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.partition import PartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.origin import RemoteInstigatorOrigin
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    asset_daemon_cursor_to_instigator_serialized_cursor,
)
from dagster._time import get_current_datetime
from dagster._vendored.dateutil.relativedelta import relativedelta
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

        now = get_current_datetime()
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
            (now - relativedelta(days=1, hours=1)).timestamp(),
            evaluation_id=2,
        )

        _create_tick(
            graphql_context.instance,
            TickStatus.SKIPPED,
            (now - relativedelta(days=2, hours=1)).timestamp(),
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


FRAGMENTS = """
fragment evaluationFields on AssetConditionEvaluation {
    rootUniqueId
    evaluationNodes {
        ... on UnpartitionedAssetConditionEvaluationNode {
            description
            startTimestamp
            endTimestamp
            status
            uniqueId
            childUniqueIds
        }
        ... on PartitionedAssetConditionEvaluationNode {
            description
            startTimestamp
            endTimestamp
            numTrue
            uniqueId
            childUniqueIds
        }
        ... on SpecificPartitionAssetConditionEvaluationNode {
            description
            status
            uniqueId
            childUniqueIds
        }
    }
}
"""

AUTO_MATERIALIZE_POLICY_SENSORS_QUERY = """
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


LEGACY_QUERY = (
    FRAGMENTS
    + """
query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    assetNodeOrError(assetKey: $assetKey) {
        ... on AssetNode {
            currentAutoMaterializeEvaluationId
        }
    }
    assetConditionEvaluationRecordsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
        ... on AssetConditionEvaluationRecords {
            records {
                evaluationId
                numRequested
                assetKey {
                    path
                }
                evaluation {
                    ...evaluationFields
                }
            }
        }
    }
}
"""
)

LEGACY_QUERY_FOR_SPECIFIC_PARTITION = (
    FRAGMENTS
    + """
query GetPartitionEvaluationQuery($assetKey: AssetKeyInput!, $partition: String!, $evaluationId: Int!) {
    assetConditionEvaluationForPartition(assetKey: $assetKey, partition: $partition, evaluationId: $evaluationId) {
        ...evaluationFields
    }
}
"""
)

LEGACY_QUERY_FOR_EVALUATION_ID = (
    FRAGMENTS
    + """
query GetEvaluationsForEvaluationIdQuery($evaluationId: Int!) {
    assetConditionEvaluationsForEvaluationId(evaluationId: $evaluationId) {
        ... on AssetConditionEvaluationRecords {
            records {
                evaluationId
                numRequested
                assetKey {
                    path
                }
                evaluation {
                    ...evaluationFields
                }
            }
        }
    }
}
"""
)

QUERY = """
query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    assetConditionEvaluationRecordsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
        ... on AssetConditionEvaluationRecords {
            records {
                evaluationId
                isLegacy
                numRequested
                assetKey {
                    path
                }
                rootUniqueId
                evaluationNodes {
                    userLabel
                    expandedLabel
                    startTimestamp
                    endTimestamp
                    numTrue
                    uniqueId
                    childUniqueIds
                }
            }
        }
    }
}
"""

TRUE_PARTITIONS_QUERY = """
query GetTruePartitions($assetKey: AssetKeyInput!, $evaluationId: Int!, $nodeUniqueId: String!) {
    truePartitionsForAutomationConditionEvaluationNode(assetKey: $assetKey, evaluationId: $evaluationId, nodeUniqueId: $nodeUniqueId)
}
"""


class TestAssetConditionEvaluations(ExecutingGraphQLContextTestMatrix):
    def test_auto_materialize_sensor(self, graphql_context: WorkspaceRequestContext):
        sensor_origin = RemoteInstigatorOrigin(
            repository_origin=infer_repository(graphql_context).get_remote_origin(),
            instigator_name="my_auto_materialize_sensor",
        )

        check.not_none(graphql_context.instance.schedule_storage).add_instigator_state(
            InstigatorState(
                sensor_origin,
                InstigatorType.SENSOR,
                status=InstigatorStatus.RUNNING,
                instigator_data=SensorInstigatorData(
                    sensor_type=SensorType.AUTO_MATERIALIZE,
                    cursor=asset_daemon_cursor_to_instigator_serialized_cursor(
                        AssetDaemonCursor.empty(12345)
                    ),
                ),
            )
        )

        with patch(
            graphql_context.instance.__class__.__module__
            + "."
            + graphql_context.instance.__class__.__name__
            + ".auto_materialize_use_sensors",
            new_callable=PropertyMock,
        ) as mock_my_property:
            mock_my_property.return_value = False

            results = execute_dagster_graphql(
                graphql_context,
                AUTO_MATERIALIZE_POLICY_SENSORS_QUERY,
                variables={
                    "assetKey": {"path": ["fresh_diamond_bottom"]},
                },
            )
            assert not results.data["assetNodeOrError"]["currentAutoMaterializeEvaluationId"]

        with patch(
            graphql_context.instance.__class__.__module__
            + "."
            + graphql_context.instance.__class__.__name__
            + ".auto_materialize_use_sensors",
            new_callable=PropertyMock,
        ) as mock_my_property:
            mock_my_property.return_value = True
            results = execute_dagster_graphql(
                graphql_context,
                AUTO_MATERIALIZE_POLICY_SENSORS_QUERY,
                variables={
                    "assetKey": {"path": ["fresh_diamond_bottom"]},
                },
            )

            assert any(
                instigator["name"] == "my_auto_materialize_sensor"
                for instigator in results.data["assetNodeOrError"]["targetingInstigators"]
            )
            assert results.data["assetNodeOrError"]["currentAutoMaterializeEvaluationId"] == 12345

    def _get_node(
        self, unique_id: str, evaluations: Sequence[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        return next(iter([node for node in evaluations if node["uniqueId"] == unique_id]))

    def _get_condition_evaluation(
        self,
        asset_key: AssetKey,
        description: str,
        partitions_def: PartitionsDefinition,
        true_partition_keys: Sequence[str],
        candidate_partition_keys: Optional[Sequence[str]] = None,
        child_evaluations: Optional[Sequence[AutomationConditionEvaluation]] = None,
    ) -> AutomationConditionEvaluation:
        return AutomationConditionEvaluation(
            condition_snapshot=AutomationConditionNodeSnapshot(
                class_name="...",
                description=description,
                unique_id=str(random.randint(0, 100000000)),
            ),
            true_subset=SerializableEntitySubset(
                key=asset_key,
                value=partitions_def.subset_with_partition_keys(true_partition_keys),
            ),
            candidate_subset=SerializableEntitySubset(
                key=asset_key,
                value=partitions_def.subset_with_partition_keys(candidate_partition_keys),
            )
            if candidate_partition_keys
            else HistoricalAllPartitionsSubsetSentinel(),
            start_timestamp=123,
            end_timestamp=456,
            child_evaluations=child_evaluations or [],
            subsets_with_metadata=[],
        )

    def test_get_evaluations_with_partitions(self, graphql_context: WorkspaceRequestContext):
        asset_key = AssetKey("upstream_static_partitioned_asset")
        partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d", "e", "f"])
        results = execute_dagster_graphql(
            graphql_context,
            LEGACY_QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "limit": 10,
                "cursor": None,
            },
        )
        assert results.data["assetConditionEvaluationRecordsOrError"] == {"records": []}

        evaluation = self._get_condition_evaluation(
            asset_key,
            "All of",
            partitions_def,
            ["a", "b"],
            child_evaluations=[
                self._get_condition_evaluation(
                    asset_key,
                    "Any of",
                    partitions_def,
                    ["a", "b", "c"],
                    child_evaluations=[
                        self._get_condition_evaluation(
                            asset_key, "parent_updated", partitions_def, ["a", "c"]
                        ),
                        self._get_condition_evaluation(asset_key, "missing", partitions_def, ["b"]),
                        self._get_condition_evaluation(asset_key, "other", partitions_def, []),
                    ],
                ),
                self._get_condition_evaluation(
                    asset_key,
                    "Not",
                    partitions_def,
                    ["a", "b"],
                    candidate_partition_keys=["a", "b", "c"],
                    child_evaluations=[
                        self._get_condition_evaluation(
                            asset_key,
                            "Any of",
                            partitions_def,
                            ["c"],
                            ["a", "b", "c"],
                            child_evaluations=[
                                self._get_condition_evaluation(
                                    asset_key,
                                    "parent missing",
                                    partitions_def,
                                    ["c"],
                                    ["a", "b", "c"],
                                ),
                                self._get_condition_evaluation(
                                    asset_key,
                                    "parent outdated",
                                    partitions_def,
                                    [],
                                    ["a", "b", "c"],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutomationConditionEvaluationWithRunIds(
                    evaluation=evaluation, run_ids=frozenset({"runid1", "runid2"})
                )
            ],
        )

        results = execute_dagster_graphql(
            graphql_context,
            LEGACY_QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "limit": 10,
                "cursor": None,
            },
        )

        records = results.data["assetConditionEvaluationRecordsOrError"]["records"]
        assert len(records) == 1

        assert records[0]["numRequested"] == 2
        evaluation = records[0]["evaluation"]

        # all nodes in the tree
        assert len(evaluation["evaluationNodes"]) == 9

        rootNode = evaluation["evaluationNodes"][0]
        assert rootNode["uniqueId"] == evaluation["rootUniqueId"]
        assert rootNode["description"] == "All of"
        assert rootNode["numTrue"] == 2
        assert len(rootNode["childUniqueIds"]) == 2

        notNode = self._get_node(rootNode["childUniqueIds"][1], evaluation["evaluationNodes"])
        assert notNode["description"] == "Not"
        assert notNode["numTrue"] == 2

        skipNode = self._get_node(notNode["childUniqueIds"][0], evaluation["evaluationNodes"])
        assert skipNode["description"] == "Any of"
        assert skipNode["numTrue"] == 1

        evaluationId = records[0]["evaluationId"]
        uniqueId = skipNode["uniqueId"]
        results = execute_dagster_graphql(
            graphql_context,
            TRUE_PARTITIONS_QUERY,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "evaluationId": evaluationId,
                "nodeUniqueId": uniqueId,
            },
        )

        assert set(results.data["truePartitionsForAutomationConditionEvaluationNode"]) == {"c"}

        # test one of the true partitions
        specific_result = execute_dagster_graphql(
            graphql_context,
            LEGACY_QUERY_FOR_SPECIFIC_PARTITION,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "partition": "b",
                "evaluationId": 10,
            },
        )

        evaluation = specific_result.data["assetConditionEvaluationForPartition"]
        assert len(evaluation["evaluationNodes"]) == 9

        rootNode = evaluation["evaluationNodes"][0]
        assert rootNode["uniqueId"] == evaluation["rootUniqueId"]

        assert rootNode["description"] == "All of"
        assert rootNode["status"] == "TRUE"
        assert len(rootNode["childUniqueIds"]) == 2

        notNode = self._get_node(rootNode["childUniqueIds"][1], evaluation["evaluationNodes"])
        assert notNode["description"] == "Not"
        assert notNode["status"] == "TRUE"

        skipNode = self._get_node(notNode["childUniqueIds"][0], evaluation["evaluationNodes"])
        assert skipNode["description"] == "Any of"
        assert skipNode["status"] == "FALSE"

        # test one of the false partitions
        specific_result = execute_dagster_graphql(
            graphql_context,
            LEGACY_QUERY_FOR_SPECIFIC_PARTITION,
            variables={
                "assetKey": {"path": ["upstream_static_partitioned_asset"]},
                "partition": "d",
                "evaluationId": 10,
            },
        )

        evaluation = specific_result.data["assetConditionEvaluationForPartition"]
        assert len(evaluation["evaluationNodes"]) == 9

        rootNode = evaluation["evaluationNodes"][0]
        assert rootNode["uniqueId"] == evaluation["rootUniqueId"]

        assert rootNode["description"] == "All of"
        assert rootNode["status"] == "FALSE"
        assert len(rootNode["childUniqueIds"]) == 2

        notNode = self._get_node(rootNode["childUniqueIds"][1], evaluation["evaluationNodes"])
        assert notNode["description"] == "Not"
        assert notNode["status"] == "SKIPPED"

        skipNode = self._get_node(notNode["childUniqueIds"][0], evaluation["evaluationNodes"])
        assert skipNode["description"] == "Any of"
        assert skipNode["status"] == "SKIPPED"

    def test_get_evaluations_with_partitions_updated(
        self, graphql_context: WorkspaceRequestContext
    ):
        @asset(
            partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]),
            automation_condition=AutomationCondition.eager().with_label("blah"),
            deps=["up"],
        )
        def A() -> None: ...

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["A"]}, "limit": 10, "cursor": None},
        )
        assert results.data == {"assetConditionEvaluationRecordsOrError": {"records": []}}

        result = evaluate_automation_conditions([A], DagsterInstance.ephemeral())

        check.not_none(
            graphql_context.instance.schedule_storage
        ).add_auto_materialize_asset_evaluations(
            evaluation_id=10,
            asset_evaluations=[
                AutomationConditionEvaluationWithRunIds(
                    evaluation=result.results[0].serializable_evaluation,
                    run_ids=frozenset({"runid1"}),
                )
            ],
        )

        results = execute_dagster_graphql(
            graphql_context,
            QUERY,
            variables={"assetKey": {"path": ["A"]}, "limit": 10, "cursor": None},
        )

        records = results.data["assetConditionEvaluationRecordsOrError"]["records"]
        assert len(records) == 1

        record = records[0]
        assert not record["isLegacy"]
        assert record["numRequested"] == 0

        # all nodes in the tree
        assert len(record["evaluationNodes"]) == 35

        rootNode = record["evaluationNodes"][0]
        assert rootNode["uniqueId"] == record["rootUniqueId"]
        assert rootNode["userLabel"] == "blah"
        assert rootNode["expandedLabel"] == [
            "(in_latest_time_window)",
            "AND",
            "(((newly_missing) OR (any_deps_updated)) SINCE (handled))",
            "AND",
            "(NOT (any_deps_missing))",
            "AND",
            "(NOT (any_deps_in_progress))",
            "AND",
            "(NOT (in_progress))",
        ]
        assert rootNode["numTrue"] == 0
        assert len(rootNode["childUniqueIds"]) == 5

        def _get_node(id):
            return next(n for n in record["evaluationNodes"] if n["uniqueId"] == id)

        not_any_deps_missing_node = _get_node(rootNode["childUniqueIds"][2])
        any_deps_missing_node = _get_node(not_any_deps_missing_node["childUniqueIds"][0])
        up_node = _get_node(any_deps_missing_node["childUniqueIds"][0])
        assert up_node["expandedLabel"] == ["up", "((missing) AND (NOT (will_be_requested)))"]

        evaluationId = record["evaluationId"]
        uniqueId = rootNode["uniqueId"]
        results = execute_dagster_graphql(
            graphql_context,
            TRUE_PARTITIONS_QUERY,
            variables={
                "assetKey": {"path": ["A"]},
                "evaluationId": evaluationId,
                "nodeUniqueId": uniqueId,
            },
        )
        assert set(results.data["truePartitionsForAutomationConditionEvaluationNode"]) == set()

        childNode = record["evaluationNodes"][1]
        assert childNode["userLabel"] is None
        assert childNode["expandedLabel"] == ["in_latest_time_window"]
        assert childNode["numTrue"] == 4
        assert len(childNode["childUniqueIds"]) == 0

        evaluationId = record["evaluationId"]
        uniqueId = childNode["uniqueId"]
        results = execute_dagster_graphql(
            graphql_context,
            TRUE_PARTITIONS_QUERY,
            variables={
                "assetKey": {"path": ["A"]},
                "evaluationId": evaluationId,
                "nodeUniqueId": uniqueId,
            },
        )

        assert set(results.data["truePartitionsForAutomationConditionEvaluationNode"]) == {
            "a",
            "b",
            "c",
            "d",
        }
