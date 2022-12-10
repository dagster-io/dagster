from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

from dagster import Definitions, StaticPartitionsDefinition, asset
from dagster._core.execution.asset_backfill import AssetBackfillData
from dagster._core.test_utils import instance_for_test


def get_repo():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset(partitions_def=partitions_def)
    def asset2():
        ...

    return Definitions(assets=[asset1, asset2]).get_repository_def()


def test_launch_asset_backfill():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            assert result
            assert result.data
            error_msg = (
                (
                    "".join(result.data["launchPartitionBackfill"]["stack"])
                    + result.data["launchPartitionBackfill"]["message"]
                )
                if "message" in result.data["launchPartitionBackfill"]
                else None
            )
            assert "backfillId" in result.data["launchPartitionBackfill"], error_msg

            backfill_id = result.data["launchPartitionBackfill"]["backfillId"]
            assert result.data["launchPartitionBackfill"]["launchedRunIds"] is None

            backfills = instance.get_backfills()
            assert len(backfills) == 1
            backfill = backfills[0]
            assert backfill.backfill_id == backfill_id
            assert backfill.serialized_asset_backfill_data
            asset_backfill_data = AssetBackfillData.from_serialized(
                backfill.serialized_asset_backfill_data, repo.asset_graph
            )
            assert asset_backfill_data.target_subsets_by_asset_key.keys() == all_asset_keys
