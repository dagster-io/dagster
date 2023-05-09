from typing import Optional, Tuple

from dagster import (
    AssetKey,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.execution.asset_backfill import AssetBackfillData
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
    GqlResult,
    define_out_of_process_context,
    execute_dagster_graphql,
)

GET_PARTITION_BACKFILLS_QUERY = """
  query InstanceBackfillsQuery($cursor: String, $limit: Int) {
    partitionBackfillsOrError(cursor: $cursor, limit: $limit) {
      ... on PartitionBackfills {
        results {
          id
          status
          numPartitions
          timestamp
          partitionNames
          partitionSetName
          partitionSet {
            id
            name
            mode
            pipelineName
            repositoryOrigin {
              id
              repositoryName
              repositoryLocationName
            }
          }
        }
      }
    }
  }
"""

SINGLE_BACKFILL_QUERY = """
  query SingleBackfillQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        partitionStatuses {
          results {
            id
            partitionName
            runId
            runStatus
          }
        }
      }
    }
  }
"""

ASSET_BACKFILL_DATA_QUERY = """
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        assetBackfillData {
            rootAssetTargetedRanges {
                start
                end
            }
            rootAssetTargetedPartitions
        }
        isAssetBackfill
      }
    }
  }
"""


def get_repo() -> RepositoryDefinition:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset(partitions_def=partitions_def)
    def asset2():
        ...

    return Definitions(assets=[asset1, asset2]).get_repository_def()


def get_repo_with_non_partitioned_asset() -> RepositoryDefinition:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset
    def asset2(asset1):
        ...

    return Definitions(assets=[asset1, asset2]).get_repository_def()


def get_repo_with_root_assets_different_partitions() -> RepositoryDefinition:
    from dagster_tests.definitions_tests.asset_reconciliation_tests.exotic_partition_mapping_scenarios import (
        root_assets_different_partitions_same_downstream,
    )

    return Definitions(assets=root_assets_different_partitions_same_downstream).get_repository_def()


def test_launch_asset_backfill_read_only_context():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        # read-only context fails
        with define_out_of_process_context(
            __file__, "get_repo", instance, read_only=True
        ) as read_only_context:
            assert read_only_context.read_only
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                read_only_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            assert launch_backfill_result
            assert launch_backfill_result.data

            assert (
                launch_backfill_result.data["launchPartitionBackfill"]["__typename"]
                == "UnauthorizedError"
            )


def test_launch_asset_backfill_all_partitions():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                        "allPartitions": True,
                    }
                },
            )

            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            assert target_subset.asset_keys == all_asset_keys
            all_partition_keys = {"a", "b", "c"}
            assert (
                target_subset.get_partitions_subset(AssetKey("asset1")).get_partition_keys()
                == all_partition_keys
            )
            assert (
                target_subset.get_partitions_subset(AssetKey("asset2")).get_partition_keys()
                == all_partition_keys
            )


def test_launch_asset_backfill_all_partitions_asset_selection():
    repo = get_repo()

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "assetSelection": [AssetKey("asset2").to_graphql_input()],
                        "allPartitions": True,
                    }
                },
            )

            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            assert target_subset.asset_keys == {AssetKey("asset2")}
            all_partition_keys = {"a", "b", "c"}
            assert (
                target_subset.get_partitions_subset(AssetKey("asset2")).get_partition_keys()
                == all_partition_keys
            )
            assert not target_subset.get_partitions_subset(AssetKey("asset1")).get_partition_keys()


def test_launch_asset_backfill_all_partitions_root_assets_different_partitions():
    repo = get_repo_with_root_assets_different_partitions()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_root_assets_different_partitions", instance
        ) as context:
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                        "allPartitions": True,
                    }
                },
            )

            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            assert target_subset.get_partitions_subset(AssetKey("root1")).get_partition_keys() == {
                "a",
                "b",
            }
            assert target_subset.get_partitions_subset(AssetKey("root2")).get_partition_keys() == {
                "1",
                "2",
            }
            assert target_subset.get_partitions_subset(
                AssetKey("downstream")
            ).get_partition_keys() == {"a", "b"}


def test_launch_asset_backfill():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            assert asset_backfill_data.target_subset.asset_keys == all_asset_keys

            # on PartitionBackfills
            get_backfills_result = execute_dagster_graphql(
                context, GET_PARTITION_BACKFILLS_QUERY, variables={}
            )
            assert not get_backfills_result.errors
            assert get_backfills_result.data
            backfill_results = get_backfills_result.data["partitionBackfillsOrError"]["results"]
            assert len(backfill_results) == 1
            assert backfill_results[0]["numPartitions"] == 2
            assert backfill_results[0]["id"] == backfill_id
            assert backfill_results[0]["partitionSet"] is None
            assert backfill_results[0]["partitionSetName"] is None
            assert set(backfill_results[0]["partitionNames"]) == {"a", "b"}

            # on PartitionBackfill
            single_backfill_result = execute_dagster_graphql(
                context, SINGLE_BACKFILL_QUERY, variables={"backfillId": backfill_id}
            )
            assert not single_backfill_result.errors
            assert single_backfill_result.data
            partition_status_results = single_backfill_result.data["partitionBackfillOrError"][
                "partitionStatuses"
            ]["results"]
            assert len(partition_status_results) == 2
            assert {
                partition_status_result["partitionName"]
                for partition_status_result in partition_status_results
            } == {"a", "b"}


def test_remove_partitions_defs_after_backfill():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            assert asset_backfill_data.target_subset.asset_keys == all_asset_keys

        with define_out_of_process_context(
            __file__, "get_repo_with_non_partitioned_asset", instance
        ) as context:
            # on PartitionBackfills
            get_backfills_result = execute_dagster_graphql(
                context, GET_PARTITION_BACKFILLS_QUERY, variables={}
            )
            assert not get_backfills_result.errors
            assert get_backfills_result.data
            backfill_results = get_backfills_result.data["partitionBackfillsOrError"]["results"]
            assert len(backfill_results) == 1
            assert backfill_results[0]["numPartitions"] == 0
            assert backfill_results[0]["id"] == backfill_id
            assert backfill_results[0]["partitionSet"] is None
            assert backfill_results[0]["partitionSetName"] is None
            assert set(backfill_results[0]["partitionNames"]) == set()

            # on PartitionBackfill
            single_backfill_result = execute_dagster_graphql(
                context, SINGLE_BACKFILL_QUERY, variables={"backfillId": backfill_id}
            )
            assert not single_backfill_result.errors
            assert single_backfill_result.data
            partition_status_results = single_backfill_result.data["partitionBackfillOrError"][
                "partitionStatuses"
            ]["results"]
            assert len(partition_status_results) == 0
            assert {
                partition_status_result["partitionName"]
                for partition_status_result in partition_status_results
            } == set()


def test_launch_asset_backfill_with_non_partitioned_asset():
    repo = get_repo_with_non_partitioned_asset()
    all_asset_keys = repo.asset_graph.all_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_non_partitioned_asset", instance
        ) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            assert target_subset.asset_keys == all_asset_keys
            assert target_subset.get_partitions_subset(AssetKey("asset1")).get_partition_keys() == {
                "a",
                "b",
            }
            assert AssetKey("asset2") in target_subset.non_partitioned_asset_keys
            assert AssetKey("asset2") not in target_subset.partitions_subsets_by_asset_key


def get_daily_hourly_repo() -> RepositoryDefinition:
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly):
        ...

    return Definitions(assets=[hourly, daily]).get_repository_def()


def test_launch_asset_backfill_with_upstream_anchor_asset():
    repo = get_daily_hourly_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    hourly_partitions = ["2020-01-02-23:00", "2020-01-02-22:00", "2020-01-03-00:00"]

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_daily_hourly_repo", instance) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": hourly_partitions,
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            asset_graph = target_subset.asset_graph
            assert target_subset == AssetGraphSubset(
                target_subset.asset_graph,
                partitions_subsets_by_asset_key={
                    AssetKey("hourly"): asset_graph.get_partitions_def(
                        AssetKey("hourly")
                    ).subset_with_partition_keys(hourly_partitions),
                    AssetKey("daily"): asset_graph.get_partitions_def(
                        AssetKey("daily")
                    ).subset_with_partition_keys(["2020-01-02", "2020-01-03"]),
                },
            )

            # on PartitionBackfills
            get_backfills_result = execute_dagster_graphql(
                context, GET_PARTITION_BACKFILLS_QUERY, variables={}
            )
            assert not get_backfills_result.errors
            assert get_backfills_result.data
            backfill_results = get_backfills_result.data["partitionBackfillsOrError"]["results"]
            assert len(backfill_results) == 1
            assert backfill_results[0]["numPartitions"] is None
            assert backfill_results[0]["id"] == backfill_id
            assert backfill_results[0]["partitionSet"] is None
            assert backfill_results[0]["partitionSetName"] is None
            assert backfill_results[0]["partitionNames"] is None


def get_daily_two_hourly_repo() -> RepositoryDefinition:
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly1():
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly2():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly1, hourly2):
        ...

    return Definitions(assets=[hourly1, hourly2, daily]).get_repository_def()


def test_launch_asset_backfill_with_two_anchor_assets():
    repo = get_daily_two_hourly_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    hourly_partitions = ["2020-01-02-23:00", "2020-01-02-22:00", "2020-01-03-00:00"]

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_daily_two_hourly_repo", instance
        ) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": hourly_partitions,
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            asset_graph = target_subset.asset_graph
            assert target_subset == AssetGraphSubset(
                target_subset.asset_graph,
                partitions_subsets_by_asset_key={
                    AssetKey("hourly1"): asset_graph.get_partitions_def(
                        AssetKey("hourly1")
                    ).subset_with_partition_keys(hourly_partitions),
                    AssetKey("hourly2"): asset_graph.get_partitions_def(
                        AssetKey("hourly2")
                    ).subset_with_partition_keys(hourly_partitions),
                    AssetKey("daily"): asset_graph.get_partitions_def(
                        AssetKey("daily")
                    ).subset_with_partition_keys(["2020-01-02", "2020-01-03"]),
                },
            )


def get_daily_hourly_non_partitioned_repo() -> RepositoryDefinition:
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly):
        ...

    @asset
    def non_partitioned(hourly):
        ...

    return Definitions(assets=[hourly, daily, non_partitioned]).get_repository_def()


def test_launch_asset_backfill_with_upstream_anchor_asset_and_non_partitioned_asset():
    repo = get_daily_hourly_non_partitioned_repo()
    all_asset_keys = repo.asset_graph.all_asset_keys

    hourly_partitions = ["2020-01-02-23:00", "2020-01-02-22:00", "2020-01-03-00:00"]

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_daily_hourly_non_partitioned_repo", instance
        ) as context:
            # launchPartitionBackfill
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": hourly_partitions,
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            asset_graph = target_subset.asset_graph
            assert target_subset == AssetGraphSubset(
                target_subset.asset_graph,
                non_partitioned_asset_keys={AssetKey("non_partitioned")},
                partitions_subsets_by_asset_key={
                    AssetKey("hourly"): asset_graph.get_partitions_def(AssetKey("hourly"))
                    .empty_subset()
                    .with_partition_keys(hourly_partitions),
                    AssetKey("daily"): asset_graph.get_partitions_def(AssetKey("daily"))
                    .empty_subset()
                    .with_partition_keys(["2020-01-02", "2020-01-03"]),
                },
            )

            asset_backfill_data_result = execute_dagster_graphql(
                context, ASSET_BACKFILL_DATA_QUERY, variables={"backfillId": backfill_id}
            )
            assert asset_backfill_data_result.data
            assert (
                asset_backfill_data_result.data["partitionBackfillOrError"]["isAssetBackfill"]
                is True
            )
            targeted_ranges = asset_backfill_data_result.data["partitionBackfillOrError"][
                "assetBackfillData"
            ]["rootAssetTargetedRanges"]
            assert len(targeted_ranges) == 1
            assert targeted_ranges[0]["start"] == "2020-01-02-22:00"
            assert targeted_ranges[0]["end"] == "2020-01-03-00:00"


def _get_backfill_data(
    launch_backfill_result: GqlResult, instance: DagsterInstance, repo
) -> Tuple[str, AssetBackfillData]:
    assert launch_backfill_result
    assert launch_backfill_result.data
    assert (
        "backfillId" in launch_backfill_result.data["launchPartitionBackfill"]
    ), _get_error_message(launch_backfill_result)

    backfill_id = launch_backfill_result.data["launchPartitionBackfill"]["backfillId"]

    backfills = instance.get_backfills()
    assert len(backfills) == 1
    backfill = backfills[0]
    assert backfill.backfill_id == backfill_id
    assert backfill.serialized_asset_backfill_data

    return backfill_id, AssetBackfillData.from_serialized(
        backfill.serialized_asset_backfill_data, repo.asset_graph, backfill.backfill_timestamp
    )


def _get_error_message(launch_backfill_result: GqlResult) -> Optional[str]:
    return (
        (
            "".join(launch_backfill_result.data["launchPartitionBackfill"]["stack"])
            + launch_backfill_result.data["launchPartitionBackfill"]["message"]
        )
        if "message" in launch_backfill_result.data["launchPartitionBackfill"]
        else None
    )
