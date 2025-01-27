import datetime
import json

from dagster import StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
    backcompat_deserialize_asset_daemon_cursor_str,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._serdes.serdes import deserialize_value, serialize_value

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_asset_reconciliation_cursor_evaluation_id_backcompat() -> None:
    # we no longer attempt to deserialize asset information from this super-old cursor format
    # instead, the next tick after a transition will just start from a clean slate (preserving
    # the evaluation id)
    backcompat_serialized = (
        """[20, ["a"], {"my_asset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]"""
    )

    assert backcompat_deserialize_asset_daemon_cursor_str(
        backcompat_serialized, None, 0
    ) == AssetDaemonCursor.empty(20)

    asset_graph = AssetGraph.from_assets([my_asset])
    c = backcompat_deserialize_asset_daemon_cursor_str(backcompat_serialized, asset_graph, 0)

    assert c == AssetDaemonCursor.empty(20)

    c2 = c.with_updates(21, datetime.datetime.now().timestamp(), [], [])

    serdes_c2 = deserialize_value(serialize_value(c2), as_type=AssetDaemonCursor)
    assert serdes_c2 == c2
    assert serdes_c2.evaluation_id == 21


def test_asset_reconciliation_cursor_evaluation_id_backcompat2() -> None:
    backcompat_serialized = """{"latest_storage_id": 50, "evaluation_id": 20, "latest_evaluation_by_asset_key": {"hourly_to_daily_1_45": "{\\"__class__\\": \\"AutoMaterializeAssetEvaluation\\", \\"asset_key\\": {\\"__class__\\": \\"AssetKey\\", \\"path\\": [\\"hourly_to_daily_1_45\\"]}, \\"num_discarded\\": 0, \\"num_requested\\": 0, \\"num_skipped\\": 0, \\"partition_subsets_by_condition\\": [[{\\"__class__\\": \\"AutoMaterializeRuleEvaluation\\", \\"evaluation_data\\": {\\"__class__\\": \\"WaitingOnAssetsRuleEvaluationData\\", \\"waiting_on_asset_keys\\": {\\"__frozenset__\\": [{\\"__class__\\": \\"AssetKey\\", \\"path\\": [\\"hourly_to_daily_0_8\\"]}]}}, \\"rule_snapshot\\": {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnParentMissingRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"waiting on upstream data to be present\\"}}, {\\"__class__\\": \\"SerializedPartitionsSubset\\", \\"serialized_partitions_def_class_name\\": \\"TimeWindowPartitionsDefinition\\", \\"serialized_partitions_def_unique_id\\": \\"241c72b8dcaedd1676326a771544c0501246866b\\", \\"serialized_subset\\": \\"{\\\\\\"version\\\\\\": 1, \\\\\\"time_windows\\\\\\": [[1701313200.0, 1701316800.0], [1701320400.0, 1701324000.0], [1701338400.0, 1701342000.0]], \\\\\\"num_partitions\\\\\\": 3}\\"}], [{\\"__class__\\": \\"AutoMaterializeRuleEvaluation\\", \\"evaluation_data\\": {\\"__class__\\": \\"WaitingOnAssetsRuleEvaluationData\\", \\"waiting_on_asset_keys\\": {\\"__frozenset__\\": [{\\"__class__\\": \\"AssetKey\\", \\"path\\": [\\"hourly_to_daily_0_8\\"]}, {\\"__class__\\": \\"AssetKey\\", \\"path\\": [\\"hourly_to_daily_0_9\\"]}]}}, \\"rule_snapshot\\": {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnParentMissingRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"waiting on upstream data to be present\\"}}, {\\"__class__\\": \\"SerializedPartitionsSubset\\", \\"serialized_partitions_def_class_name\\": \\"TimeWindowPartitionsDefinition\\", \\"serialized_partitions_def_unique_id\\": \\"241c72b8dcaedd1676326a771544c0501246866b\\", \\"serialized_subset\\": \\"{\\\\\\"version\\\\\\": 1, \\\\\\"time_windows\\\\\\": [[1701316800.0, 1701320400.0], [1701331200.0, 1701334800.0]], \\\\\\"num_partitions\\\\\\": 2}\\"}]], \\"rule_snapshots\\": [{\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnParentMissingRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"waiting on upstream data to be present\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnParentOutdatedRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"waiting on upstream data to be up to date\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnRequiredButNonexistentParentsRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"required parent partitions do not exist\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"MaterializeOnRequiredForFreshnessRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.MATERIALIZE\\"}, \\"description\\": \\"required to meet this or downstream asset's freshness policy\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"MaterializeOnMissingRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.MATERIALIZE\\"}, \\"description\\": \\"materialization is missing\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"MaterializeOnParentUpdatedRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.MATERIALIZE\\"}, \\"description\\": \\"upstream data has changed since latest materialization\\"}, {\\"__class__\\": \\"AutoMaterializeRuleSnapshot\\", \\"class_name\\": \\"SkipOnBackfillInProgressRule\\", \\"decision_type\\": {\\"__enum__\\": \\"AutoMaterializeDecisionType.SKIP\\"}, \\"description\\": \\"targeted by an in-progress backfill\\"}], \\"run_ids\\": {\\"__set__\\": []}}"}}"""

    assert backcompat_deserialize_asset_daemon_cursor_str(
        backcompat_serialized, None, 0
    ) == AssetDaemonCursor.empty(20)


def test_asset_reconciliation_cursor_auto_observe_backcompat() -> None:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1(): ...

    @asset
    def asset2(): ...

    handled_root_partitions_by_asset_key = {
        asset1.key: partitions_def.subset_with_partition_keys(["a", "b"])
    }
    handled_root_asset_keys = {asset2.key}
    serialized = json.dumps(
        (
            25,
            [key.to_user_string() for key in handled_root_asset_keys],
            {
                key.to_user_string(): subset.serialize()
                for key, subset in handled_root_partitions_by_asset_key.items()
            },
        )
    )

    cursor = backcompat_deserialize_asset_daemon_cursor_str(
        serialized, AssetGraph.from_assets([asset1, asset2]), 0
    )
    assert cursor.evaluation_id == 25
