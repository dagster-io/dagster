from typing import Optional, Tuple

import mock
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
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.backfill import execute_backfill_iteration
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
    GqlResult,
    define_out_of_process_context,
    execute_dagster_graphql,
    main_repo_location_name,
)

ensure_dagster_tests_import()
from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.scenarios.asset_graphs import (
    root_assets_different_partitions_same_downstream,
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
            rootTargetedPartitions {
                partitionKeys
                ranges {
                    start
                    end
                }
            }
        }
        isAssetBackfill
      }
    }
  }
"""

ASSET_BACKFILL_LOGS_QUERY = """
  query BackfillLogsByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        logEvents {
            events {
                message
                timestamp
                level
            }
            cursor
        }
      }
    }
  }
"""

ASSET_BACKFILL_PREVIEW_QUERY = """
query assetBackfillPreview($params: AssetBackfillPreviewParams!) {
  assetBackfillPreview(params: $params) {
    assetKey {
      path
    }
    partitions {
      partitionKeys
      ranges {
        start
        end
      }
    }
  }
}
"""


def get_repo() -> RepositoryDefinition:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1(): ...

    @asset(partitions_def=partitions_def)
    def asset2(): ...

    @asset()
    def asset3():
        """Non-partitioned asset."""
        ...

    return Definitions(assets=[asset1, asset2, asset3]).get_repository_def()


def get_repo_with_non_partitioned_asset() -> RepositoryDefinition:
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1(): ...

    @asset
    def asset2(asset1): ...

    return Definitions(assets=[asset1, asset2]).get_repository_def()


def get_repo_with_root_assets_different_partitions() -> RepositoryDefinition:
    return Definitions(assets=root_assets_different_partitions_same_downstream).get_repository_def()


def test_launch_asset_backfill_read_only_context():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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

            launch_backfill_result = execute_dagster_graphql(
                read_only_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionsByAssets": [
                            {
                                "assetKey": key.to_graphql_input(),
                                "partitions": {"range": {"start": "a", "end": "b"}},
                            }
                            for key in all_asset_keys
                        ]
                    }
                },
            )

            assert (
                launch_backfill_result.data["launchPartitionBackfill"]["__typename"]
                == "UnauthorizedError"
            )

        location_name = main_repo_location_name()

        # context with per-location permissions on the specific location succeeds
        with define_out_of_process_context(
            __file__,
            "get_repo",
            instance,
            read_only=True,
            read_only_locations={location_name: False},  # not read-only in this specific location
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
                == "LaunchBackfillSuccess"
            )

            launch_backfill_result = execute_dagster_graphql(
                read_only_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionsByAssets": [
                            {
                                "assetKey": key.to_graphql_input(),
                                "partitions": {"range": {"start": "a", "end": "b"}},
                            }
                            for key in all_asset_keys
                        ]
                    }
                },
            )

            assert launch_backfill_result
            assert launch_backfill_result.data

            assert (
                launch_backfill_result.data["launchPartitionBackfill"]["__typename"]
                == "LaunchBackfillSuccess"
            )

            # assets that aren't in the asset graph at all fail permissions check
            # because they can't be mapped to a particular code location
            launch_backfill_result = execute_dagster_graphql(
                read_only_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionNames": ["a", "b"],
                        "assetSelection": [{"path": ["doesnot", "exist"]}],
                    }
                },
            )
            assert launch_backfill_result
            assert launch_backfill_result.data

            assert (
                launch_backfill_result.data["launchPartitionBackfill"]["__typename"]
                == "UnauthorizedError"
            )

            launch_backfill_result = execute_dagster_graphql(
                read_only_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionsByAssets": [
                            {
                                "assetKey": {"path": ["doesnot", "exist"]},
                                "partitions": {"range": {"start": "a", "end": "b"}},
                            }
                        ]
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
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            assert not target_subset.get_partitions_subset(
                AssetKey("asset1"), asset_graph=repo.asset_graph
            ).get_partition_keys()


def test_launch_asset_backfill_partitions_by_asset():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionsByAssets": [
                            {
                                "assetKey": AssetKey("asset1").to_graphql_input(),
                                "partitions": {
                                    "range": {
                                        "start": "b",
                                        "end": "c",
                                    }
                                },
                            },
                            {
                                "assetKey": AssetKey("asset2").to_graphql_input(),
                            },
                            {
                                "assetKey": AssetKey("asset3").to_graphql_input(),
                            },
                        ],
                    }
                },
            )

            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset
            assert target_subset.asset_keys == all_asset_keys
            all_partition_keys = {"a", "b", "c"}
            assert target_subset.get_partitions_subset(AssetKey("asset1")).get_partition_keys() == {
                "b",
                "c",
            }
            assert (
                target_subset.get_partitions_subset(AssetKey("asset2")).get_partition_keys()
                == all_partition_keys
            )
            assert target_subset.non_partitioned_asset_keys == {AssetKey("asset3")}


def test_launch_asset_backfill_all_partitions_root_assets_different_partitions():
    repo = get_repo_with_root_assets_different_partitions()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            assert (
                single_backfill_result.data["partitionBackfillOrError"]["partitionStatuses"] is None
            )


def test_remove_partitions_defs_after_backfill_backcompat():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
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

        # Replace the asset backfill data with the backcompat serialization
        backfill = instance.get_backfills()[0]
        backcompat_backfill = backfill._replace(
            asset_backfill_data=None,
            serialized_asset_backfill_data=backfill.asset_backfill_data.serialize(
                instance, asset_graph=repo.asset_graph
            ),
        )

        with mock.patch(
            "dagster._core.instance.DagsterInstance.get_backfills",
            return_value=[backcompat_backfill],
        ):
            # When the partitions defs are unchanged, the backfill data can be fetched
            with define_out_of_process_context(__file__, "get_repo", instance) as context:
                get_backfills_result = execute_dagster_graphql(
                    context, GET_PARTITION_BACKFILLS_QUERY, variables={}
                )
                assert not get_backfills_result.errors
                assert get_backfills_result.data

                backfill_results = get_backfills_result.data["partitionBackfillsOrError"]["results"]
                assert len(backfill_results) == 1
                assert backfill_results[0]["numPartitions"] == 2
                assert backfill_results[0]["id"] == backfill_id
                assert set(backfill_results[0]["partitionNames"]) == {"a", "b"}

            # When the partitions defs are changed, the backfill data cannot be fetched
            with define_out_of_process_context(
                __file__, "get_repo_with_non_partitioned_asset", instance
            ) as context:
                get_backfills_result = execute_dagster_graphql(
                    context, GET_PARTITION_BACKFILLS_QUERY, variables={}
                )
                assert not get_backfills_result.errors
                assert get_backfills_result.data

                backfill_results = get_backfills_result.data["partitionBackfillsOrError"]["results"]
                assert len(backfill_results) == 1
                assert backfill_results[0]["numPartitions"] == 0
                assert backfill_results[0]["id"] == backfill_id
                assert set(backfill_results[0]["partitionNames"]) == set()


def test_remove_partitions_defs_after_backfill():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            assert (
                single_backfill_result.data["partitionBackfillOrError"]["partitionStatuses"] is None
            )


def test_launch_asset_backfill_with_non_partitioned_asset():
    repo = get_repo_with_non_partitioned_asset()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
    def hourly(): ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly): ...

    return Definitions(assets=[hourly, daily]).get_repository_def()


def test_launch_asset_backfill_with_upstream_anchor_asset():
    repo = get_daily_hourly_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            asset_graph = repo.asset_graph
            assert target_subset == AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    AssetKey("hourly"): asset_graph.get(
                        AssetKey("hourly")
                    ).partitions_def.subset_with_partition_keys(hourly_partitions),
                    AssetKey("daily"): asset_graph.get(
                        AssetKey("daily")
                    ).partitions_def.subset_with_partition_keys(["2020-01-02", "2020-01-03"]),
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
    def hourly1(): ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly2(): ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly1, hourly2): ...

    return Definitions(assets=[hourly1, hourly2, daily]).get_repository_def()


def test_launch_asset_backfill_with_two_anchor_assets():
    repo = get_daily_two_hourly_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            asset_graph = repo.asset_graph
            assert target_subset == AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    AssetKey("hourly1"): asset_graph.get(
                        AssetKey("hourly1")
                    ).partitions_def.subset_with_partition_keys(hourly_partitions),
                    AssetKey("hourly2"): asset_graph.get(
                        AssetKey("hourly2")
                    ).partitions_def.subset_with_partition_keys(hourly_partitions),
                    AssetKey("daily"): asset_graph.get(
                        AssetKey("daily")
                    ).partitions_def.subset_with_partition_keys(["2020-01-02", "2020-01-03"]),
                },
            )


def get_daily_hourly_non_partitioned_repo() -> RepositoryDefinition:
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
    def hourly(): ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def daily(hourly): ...

    @asset
    def non_partitioned(hourly): ...

    return Definitions(assets=[hourly, daily, non_partitioned]).get_repository_def()


def test_launch_asset_backfill_with_upstream_anchor_asset_and_non_partitioned_asset():
    repo = get_daily_hourly_non_partitioned_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            asset_graph = repo.asset_graph
            assert target_subset == AssetGraphSubset(
                non_partitioned_asset_keys={AssetKey("non_partitioned")},
                partitions_subsets_by_asset_key={
                    AssetKey("hourly"): (
                        asset_graph.get(AssetKey("hourly"))
                        .partitions_def.empty_subset()
                        .with_partition_keys(hourly_partitions)
                    ),
                    AssetKey("daily"): (
                        asset_graph.get(AssetKey("daily"))
                        .partitions_def.empty_subset()
                        .with_partition_keys(["2020-01-02", "2020-01-03"])
                    ),
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
            ]["rootTargetedPartitions"]["ranges"]
            assert len(targeted_ranges) == 1
            assert targeted_ranges[0]["start"] == "2020-01-02-22:00"
            assert targeted_ranges[0]["end"] == "2020-01-03-00:00"


def test_asset_backfill_non_existant_asset_keys():
    repo = get_daily_hourly_non_partitioned_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

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
            backfill_id, _asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
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
            ]["rootTargetedPartitions"]["ranges"]
            assert len(targeted_ranges) == 1
            assert targeted_ranges[0]["start"] == "2020-01-02-22:00"
            assert targeted_ranges[0]["end"] == "2020-01-03-00:00"

        # Load the backfill data in a different context where the targeted asset keys no longer exist
        with define_out_of_process_context(__file__, "get_repo", instance) as other_context:
            asset_backfill_data_result = execute_dagster_graphql(
                other_context, ASSET_BACKFILL_DATA_QUERY, variables={"backfillId": backfill_id}
            )
            assert asset_backfill_data_result.data
            assert (
                asset_backfill_data_result.data["partitionBackfillOrError"]["isAssetBackfill"]
                is True
            )
            assert (
                asset_backfill_data_result.data["partitionBackfillOrError"]["assetBackfillData"][
                    "rootTargetedPartitions"
                ]
                is None
            )


def test_asset_backfill_status_only_unpartitioned_assets():
    repo = get_daily_hourly_non_partitioned_repo()

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
                        "allPartitions": True,
                        "assetSelection": [AssetKey("non_partitioned").to_graphql_input()],
                    }
                },
            )
            backfill_id, asset_backfill_data = _get_backfill_data(
                launch_backfill_result, instance, repo
            )
            target_subset = asset_backfill_data.target_subset

            assert target_subset == AssetGraphSubset(
                non_partitioned_asset_keys={AssetKey("non_partitioned")},
            )

            asset_backfill_data_result = execute_dagster_graphql(
                context, ASSET_BACKFILL_DATA_QUERY, variables={"backfillId": backfill_id}
            )
            assert asset_backfill_data_result.data
            assert (
                asset_backfill_data_result.data["partitionBackfillOrError"]["isAssetBackfill"]
                is True
            )
            assert (
                asset_backfill_data_result.data["partitionBackfillOrError"]["assetBackfillData"][
                    "rootTargetedPartitions"
                ]
                is None
            )


def test_asset_backfill_preview_time_partitioned():
    repo = get_daily_hourly_non_partitioned_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

    hourly_partitions = ["2020-01-02-23:00", "2020-01-02-22:00", "2020-01-03-00:00"]

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_daily_hourly_non_partitioned_repo", instance
        ) as context:
            backfill_preview_result = execute_dagster_graphql(
                context,
                ASSET_BACKFILL_PREVIEW_QUERY,
                variables={
                    "params": {
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                        "partitionNames": hourly_partitions,
                    }
                },
            )

            target_asset_partitions = backfill_preview_result.data["assetBackfillPreview"]
            assert len(target_asset_partitions) == 3

            # Assert toposorted
            assert target_asset_partitions[0]["assetKey"] == {"path": ["hourly"]}
            assert target_asset_partitions[0]["partitions"]["ranges"] == [
                {"start": "2020-01-02-22:00", "end": "2020-01-03-00:00"}
            ]
            assert target_asset_partitions[0]["partitions"]["partitionKeys"] is None

            assert target_asset_partitions[1]["assetKey"] == {"path": ["daily"]}
            assert target_asset_partitions[1]["partitions"]["ranges"] == [
                {"start": "2020-01-02", "end": "2020-01-03"}
            ]
            assert target_asset_partitions[1]["partitions"]["partitionKeys"] is None

            assert target_asset_partitions[2]["assetKey"] == {"path": ["non_partitioned"]}
            assert target_asset_partitions[2]["partitions"] is None


def test_asset_backfill_preview_static_partitioned():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys
    partition_keys = ["a", "b"]

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo", instance) as context:
            backfill_preview_result = execute_dagster_graphql(
                context,
                ASSET_BACKFILL_PREVIEW_QUERY,
                variables={
                    "params": {
                        "partitionNames": partition_keys,
                        "assetSelection": [key.to_graphql_input() for key in all_asset_keys],
                    }
                },
            )

            target_asset_partitions = backfill_preview_result.data["assetBackfillPreview"]
            assert len(target_asset_partitions) == 3

            # Assert toposorted
            assert target_asset_partitions[0]["assetKey"] == {"path": ["asset1"]}
            assert target_asset_partitions[0]["partitions"]["ranges"] is None
            assert set(target_asset_partitions[0]["partitions"]["partitionKeys"]) == set(
                partition_keys
            )

            assert target_asset_partitions[1]["assetKey"] == {"path": ["asset2"]}
            assert target_asset_partitions[1]["partitions"]["ranges"] is None
            assert set(target_asset_partitions[1]["partitions"]["partitionKeys"]) == set(
                partition_keys
            )

            assert target_asset_partitions[2]["assetKey"] == {"path": ["asset3"]}
            assert target_asset_partitions[2]["partitions"] is None


def test_asset_backfill_error_raised_upon_invalid_params_provided():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_daily_hourly_non_partitioned_repo", instance
        ) as context:
            launch_backfill_result = execute_dagster_graphql(
                context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    "backfillParams": {
                        "partitionsByAssets": [
                            {
                                "assetKey": {"path": ["hourly"]},
                                "partitions": {
                                    "range": {
                                        "start": "2024-01-01-00:00",
                                        "end": "2024-01-01-01:00",
                                    }
                                },
                            }
                        ],
                        "assetSelection": [{"path": ["hourly"]}],
                    }
                },
            )
            assert launch_backfill_result.data
            assert (
                launch_backfill_result.data["launchPartitionBackfill"]["__typename"]
                == "PythonError"
            )
            assert (
                "partitions_by_assets cannot be used together with asset_selection, selector, or partitionNames"
                in launch_backfill_result.data["launchPartitionBackfill"]["message"]
            )


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
    assert backfill.asset_backfill_data

    return backfill_id, backfill.asset_backfill_data


def _get_error_message(launch_backfill_result: GqlResult) -> Optional[str]:
    return (
        (
            "".join(launch_backfill_result.data["launchPartitionBackfill"]["stack"])
            + launch_backfill_result.data["launchPartitionBackfill"]["message"]
        )
        if "message" in launch_backfill_result.data["launchPartitionBackfill"]
        else None
    )


def test_backfill_logs():
    repo = get_repo()
    all_asset_keys = repo.asset_graph.materializable_asset_keys

    with instance_for_test() as instance:
        # need to override this method on the instance since it defaults ot False in OSS. When we enable this
        # feature in OSS we can remove this override
        def override_backfill_storage_setting(self):
            return True

        instance.backfill_log_storage_enabled = override_backfill_storage_setting.__get__(
            instance, DagsterInstance
        )
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

            list(
                execute_backfill_iteration(
                    context.process_context, get_default_daemon_logger("BackfillDaemon")
                )
            )

            backfill_logs = execute_dagster_graphql(
                context,
                ASSET_BACKFILL_LOGS_QUERY,
                variables={
                    "backfillId": backfill_id,
                },
            )

            assert len(backfill_logs.data["partitionBackfillOrError"]["logEvents"]["events"]) > 0
