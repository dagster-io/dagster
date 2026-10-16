from collections import OrderedDict
from collections.abc import Mapping, Sequence
from unittest import mock

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.partitions.snap import (
    DynamicPartitionsSnap,
    MultiPartitionsSnap,
    PartitionDimensionSnap,
    PartitionsSnap,
    StaticPartitionsSnap,
)
from dagster._core.definitions.selector import RepositorySelector
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.implementation.execution.dynamic_partitions import (
    MultipartitionedAssetWipeTarget,
    _get_asset_keys_using_dynamic_partitions_def,
    wipe_materializations_for_deleted_partitions,
)
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.schema.errors import GrapheneUnauthorizedError
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_repository_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    NonLaunchableGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)

GET_PARTITION_SETS_FOR_PIPELINE_QUERY = """
    query PartitionSetsQuery($repositorySelector: RepositorySelector!, $pipelineName: String!) {
        partitionSetsOrError(repositorySelector: $repositorySelector, pipelineName: $pipelineName) {
            __typename
            ...on PartitionSets {
                results {
                    name
                    pipelineName
                    solidSelection
                    mode
                }
            }
            ... on PythonError {
                message
                stack
            }
            ...on PipelineNotFoundError {
                message
            }
        }
    }
"""

GET_PARTITION_SET_QUERY = """
    query PartitionSetQuery($repositorySelector: RepositorySelector!, $partitionSetName: String!) {
        partitionSetOrError(repositorySelector: $repositorySelector, partitionSetName: $partitionSetName) {
            __typename
            ... on PythonError {
                message
                stack
            }
            ...on PartitionSet {
                name
                pipelineName
                solidSelection
                mode
                partitionsOrError {
                    ... on Partitions {
                        results {
                            name
                            tagsOrError {
                                __typename
                            }
                            runConfigOrError {
                                ... on PartitionRunConfig {
                                    yaml
                                }
                            }
                        }
                    }
                    ... on PythonError {
                        message
                        stack
                    }
                }
            }
        }
    }
"""

GET_PARTITION_SET_TAGS_QUERY = """
    query PartitionSetQuery($repositorySelector: RepositorySelector!, $partitionSetName: String!) {
        partitionSetOrError(repositorySelector: $repositorySelector, partitionSetName: $partitionSetName) {
            ...on PartitionSet {
                partitionsOrError(limit: 1) {
                    ... on Partitions {
                        results {
                            tagsOrError {
                                ... on PartitionTags {
                                    results {
                                        key
                                        value
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
"""

GET_PARTITION_SET_STATUS_QUERY = """
    query PartitionSetQuery($repositorySelector: RepositorySelector!, $partitionSetName: String!) {
        partitionSetOrError(repositorySelector: $repositorySelector, partitionSetName: $partitionSetName) {
            ...on PartitionSet {
                id
                partitionStatusesOrError {
                    __typename
                    ... on PartitionStatuses {
                        results {
                            id
                            partitionName
                            runStatus
                        }
                    }
                    ... on PythonError {
                        message
                        stack
                    }
                }
            }
        }
    }
"""


ADD_DYNAMIC_PARTITION_MUTATION = """
mutation($partitionsDefName: String!, $partitionKey: String!, $repositorySelector: RepositorySelector!) {
    addDynamicPartition(partitionsDefName: $partitionsDefName, partitionKey: $partitionKey, repositorySelector: $repositorySelector) {
        __typename
        ... on AddDynamicPartitionSuccess {
            partitionsDefName
            partitionKey
        }
        ... on PythonError {
            message
            stack
        }
        ... on UnauthorizedError {
            message
        }
    }
}
"""


DELETE_DYNAMIC_PARTITIONS_MUTATION = """
mutation($partitionsDefName: String!, $partitionKeys: [String!]!, $repositorySelector: RepositorySelector!, $wipeMaterializations: Boolean) {
    deleteDynamicPartitions(partitionsDefName: $partitionsDefName, partitionKeys: $partitionKeys, repositorySelector: $repositorySelector, wipeMaterializations: $wipeMaterializations) {
        __typename
        ... on DeleteDynamicPartitionsSuccess {
            partitionsDefName
        }
        ... on PythonError {
            message
            stack
        }
        ... on UnauthorizedError {
            message
        }
        ... on UnsupportedOperationError {
            message
        }
    }
}
"""


class TestPartitionSets(NonLaunchableGraphQLContextTestMatrix):
    def test_get_partition_sets_for_pipeline(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={"repositorySelector": selector, "pipelineName": "integers"},
        )

        assert result.data
        snapshot.assert_match(result.data)

        invalid_job_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={"repositorySelector": selector, "pipelineName": "invalid_job"},
        )

        assert invalid_job_result.data
        snapshot.assert_match(invalid_job_result.data)

    def test_get_partition_set(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={
                "partitionSetName": "integers_partition_set",
                "repositorySelector": selector,
            },
        )

        assert result.data
        snapshot.assert_match(result.data)

        invalid_partition_set_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={"partitionSetName": "invalid_partition", "repositorySelector": selector},
        )

        assert (
            invalid_partition_set_result.data["partitionSetOrError"]["__typename"]
            == "PartitionSetNotFoundError"
        )
        assert invalid_partition_set_result.data

        snapshot.assert_match(invalid_partition_set_result.data)

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={
                "partitionSetName": "dynamic_partitioned_assets_job_partition_set",
                "repositorySelector": selector,
            },
        )

        assert result.data
        snapshot.assert_match(result.data)

    def test_get_partition_tags(self, graphql_context):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_TAGS_QUERY,
            variables={
                "partitionSetName": "integers_partition_set",
                "repositorySelector": selector,
            },
        )

        assert not result.errors
        assert result.data
        partitions = result.data["partitionSetOrError"]["partitionsOrError"]["results"]
        assert len(partitions) == 1
        sorted_items = sorted(partitions[0]["tagsOrError"]["results"], key=lambda item: item["key"])
        tags = OrderedDict({item["key"]: item["value"] for item in sorted_items})
        assert tags == {
            "foo": "0",
            "dagster/partition": "0",
            "dagster/partition_set": "integers_partition_set",
        }


class TestPartitionSetRuns(ExecutingGraphQLContextTestMatrix):
    def test_get_partition_status(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_STATUS_QUERY,
            variables={
                "partitionSetName": "integers_partition_set",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        partitionStatuses = result.data["partitionSetOrError"]["partitionStatusesOrError"][
            "results"
        ]
        assert len(partitionStatuses) == 10
        for partitionStatus in partitionStatuses:
            if partitionStatus["partitionName"] in ("2", "3"):
                assert partitionStatus["runStatus"] == "SUCCESS"
            else:
                assert partitionStatus["runStatus"] is None

        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": [str(num) for num in range(10)],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 10

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_STATUS_QUERY,
            variables={
                "partitionSetName": "integers_partition_set",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        partitionStatuses = result.data["partitionSetOrError"]["partitionStatusesOrError"][
            "results"
        ]
        assert len(partitionStatuses) == 10
        for partitionStatus in partitionStatuses:
            assert partitionStatus["runStatus"] == "SUCCESS"

    def test_get_status_failure_cancelation_states(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integers_partition_set",
                    },
                    "partitionNames": ["2", "3", "4"],
                    "forceSynchronousSubmission": True,
                }
            },
        )

        assert not result.errors

        runs = graphql_context.instance.get_runs()
        graphql_context.instance.report_run_failed(runs[1])
        graphql_context.instance.report_run_canceled(runs[2])

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_STATUS_QUERY,
            variables={
                "partitionSetName": "integers_partition_set",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        partitionStatuses = result.data["partitionSetOrError"]["partitionStatusesOrError"][
            "results"
        ]
        failure = 0
        canceled = 0
        success = 0
        for partitionStatus in partitionStatuses:
            if partitionStatus["runStatus"] == "FAILURE":
                failure += 1
            if partitionStatus["runStatus"] == "CANCELED":
                canceled += 1
            if partitionStatus["runStatus"] == "SUCCESS":
                success += 1

        # Note: Canceled run is not reflected in partition status
        assert failure == 1
        assert success == 1
        assert canceled == 0

    def test_get_status_time_window_partitioned_job(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "daily_partitioned_job_partition_set",
                    },
                    "partitionNames": ["2022-06-01", "2022-06-02"],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_STATUS_QUERY,
            variables={
                "partitionSetName": "daily_partitioned_job_partition_set",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        partitionStatuses = result.data["partitionSetOrError"]["partitionStatusesOrError"][
            "results"
        ]
        assert len(partitionStatuses) > 2

        for partitionStatus in partitionStatuses:
            if partitionStatus["partitionName"] in ["2022-06-01", "2022-06-02"]:
                assert partitionStatus["runStatus"] == "SUCCESS"
            else:
                assert partitionStatus["runStatus"] is None

    def test_get_status_static_partitioned_job(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "static_partitioned_job_partition_set",
                    },
                    "partitionNames": ["2", "3"],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_STATUS_QUERY,
            variables={
                "partitionSetName": "static_partitioned_job_partition_set",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        partitionStatuses = result.data["partitionSetOrError"]["partitionStatusesOrError"][
            "results"
        ]
        assert len(partitionStatuses) == 5

        for partitionStatus in partitionStatuses:
            if partitionStatus["partitionName"] in ["2", "3"]:
                assert partitionStatus["runStatus"] == "SUCCESS"
            else:
                assert partitionStatus["runStatus"] is None

    def test_add_dynamic_partitions(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            ADD_DYNAMIC_PARTITION_MUTATION,
            variables={
                "partitionsDefName": "foo",
                "partitionKey": "bar",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data["addDynamicPartition"]["__typename"] == "AddDynamicPartitionSuccess"
        assert result.data["addDynamicPartition"]["partitionsDefName"] == "foo"
        assert result.data["addDynamicPartition"]["partitionKey"] == "bar"

        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"bar"}

        result = execute_dagster_graphql(
            graphql_context,
            ADD_DYNAMIC_PARTITION_MUTATION,
            variables={
                "partitionsDefName": "foo",
                "partitionKey": "bar",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data["addDynamicPartition"]["__typename"] == "DuplicateDynamicPartitionError"

    def test_delete_dynamic_partitions(self, graphql_context):
        graphql_context.instance.add_dynamic_partitions("foo", ["bar", "biz", "baz"])

        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            DELETE_DYNAMIC_PARTITIONS_MUTATION,
            variables={
                "partitionsDefName": "foo",
                "partitionKeys": ["bar", "biz"],
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "DeleteDynamicPartitionsSuccess"
        ), str(result.data)
        assert result.data["deleteDynamicPartitions"]["partitionsDefName"] == "foo"

        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"baz"}

    def test_delete_nonexistent_dynamic_partitions_def_throws_error(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            DELETE_DYNAMIC_PARTITIONS_MUTATION,
            variables={
                "partitionsDefName": "nonexistent",
                "partitionKeys": ["bar"],
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data["deleteDynamicPartitions"]["__typename"] == "UnauthorizedError", str(
            result.data
        )
        assert (
            "does not contain a dynamic partitions definition"
            in result.data["deleteDynamicPartitions"]["message"]
        )

    def test_delete_static_partitions_def_throws_error(self, graphql_context):
        # "static" is a dimension of dynamic_in_multipartitions_def, but a static partitions
        # definition has no name, so it can never be addressed by partitionsDefName
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            DELETE_DYNAMIC_PARTITIONS_MUTATION,
            variables={
                "partitionsDefName": "static",
                "partitionKeys": ["a"],
                "repositorySelector": repository_selector,
                "wipeMaterializations": True,
            },
        )
        assert not result.errors
        assert result.data["deleteDynamicPartitions"]["__typename"] == "UnauthorizedError", str(
            result.data
        )
        assert (
            "does not contain a dynamic partitions definition"
            in result.data["deleteDynamicPartitions"]["message"]
        )

    def test_delete_dynamic_partitions_without_wipe_skips_wipe_permission_check(
        self, graphql_context
    ):
        graphql_context.instance.add_dynamic_partitions("foo", ["bar", "baz"])

        repository_selector = infer_repository_selector(graphql_context)
        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ) as mock_assert_permission,
            mock.patch.object(
                graphql_context.instance, "wipe_asset_partitions"
            ) as mock_wipe_asset_partitions,
        ):
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "foo",
                    "partitionKeys": ["bar"],
                    "repositorySelector": repository_selector,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "DeleteDynamicPartitionsSuccess"
        ), str(result.data)

        # deleting without wiping needs no wipe permission, so users who could delete
        # partitions before this argument existed are unaffected
        mock_assert_permission.assert_not_called()
        mock_wipe_asset_partitions.assert_not_called()
        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"baz"}

    def test_delete_dynamic_partitions_wipe_materializations(self, graphql_context):
        graphql_context.instance.add_dynamic_partitions("foo", ["bar", "biz", "baz"])

        repository_selector = infer_repository_selector(graphql_context)
        with mock.patch.object(
            graphql_context.instance, "wipe_asset_partitions"
        ) as mock_wipe_asset_partitions:
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "foo",
                    "partitionKeys": ["bar", "biz"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "DeleteDynamicPartitionsSuccess"
        ), str(result.data)

        # the wipe fans out to every asset partitioned by the dynamic partitions def
        wiped = {
            (call.args[0], tuple(call.args[1]))
            for call in mock_wipe_asset_partitions.call_args_list
        }
        assert wiped == {
            (AssetKey("upstream_dynamic_partitioned_asset"), ("bar", "biz")),
            (AssetKey("downstream_dynamic_partitioned_asset"), ("bar", "biz")),
        }
        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"baz"}

    def test_delete_dynamic_partitions_wipe_unsupported_storage(self, graphql_context):
        graphql_context.instance.add_dynamic_partitions("foo", ["bar", "baz"])

        repository_selector = infer_repository_selector(graphql_context)
        with mock.patch.object(
            graphql_context.instance,
            "wipe_asset_partitions",
            side_effect=NotImplementedError,
        ):
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "foo",
                    "partitionKeys": ["bar"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "UnsupportedOperationError"
        ), str(result.data)

        # the partitions were not deleted
        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"bar", "baz"}

    def test_delete_dynamic_partitions_wipe_multipartitioned_assets_unsupported(
        self, graphql_context
    ):
        graphql_context.instance.add_dynamic_partitions("dynamic", ["one", "two"])

        repository_selector = infer_repository_selector(graphql_context)
        with mock.patch.object(
            graphql_context.instance, "wipe_asset_partitions"
        ) as mock_wipe_asset_partitions:
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "dynamic",
                    "partitionKeys": ["one"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "UnsupportedOperationError"
        ), str(result.data)
        assert (
            "dimension of multi-partitioned assets"
            in result.data["deleteDynamicPartitions"]["message"]
        )

        # neither the wipe nor the deletion happened
        mock_wipe_asset_partitions.assert_not_called()
        assert set(graphql_context.instance.get_dynamic_partitions("dynamic")) == {"one", "two"}

    def test_delete_dynamic_partitions_wipe_multipartitioned_assets(self, graphql_context):
        graphql_context.instance.add_dynamic_partitions("dynamic", ["one", "two"])

        repository_selector = infer_repository_selector(graphql_context)
        with (
            mock.patch.object(
                type(graphql_context.instance),
                "supports_wipe_on_delete_for_multipartitioned_assets",
                new_callable=mock.PropertyMock,
                return_value=True,
            ),
            mock.patch.object(
                graphql_context.instance, "wipe_asset_partitions"
            ) as mock_wipe_asset_partitions,
        ):
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "dynamic",
                    "partitionKeys": ["one"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "DeleteDynamicPartitionsSuccess"
        ), str(result.data)

        # the deleted dimension key expands into one multi-partition key per key of the other
        # dimension, for every multi-partitioned asset using the definition
        wiped = {
            (call.args[0], tuple(sorted(call.args[1])))
            for call in mock_wipe_asset_partitions.call_args_list
        }
        assert wiped == {
            (
                AssetKey("dynamic_in_multipartitions_success"),
                ("one|a", "one|b", "one|c"),
            ),
            (AssetKey("dynamic_in_multipartitions_fail"), ("one|a", "one|b", "one|c")),
        }
        assert set(graphql_context.instance.get_dynamic_partitions("dynamic")) == {"two"}

    def test_delete_dynamic_partitions_wipe_even_if_partition_already_deleted(
        self, graphql_context
    ):
        # Wiping is not gated on the key still being in the partitions definition, so events
        # orphaned by an earlier delete can still be cleaned up. "a" is also a key of the
        # *static* dimension, so this doubles as a check that real partitions containing it
        # (such as "one|a") are not reached.
        graphql_context.instance.add_dynamic_partitions("dynamic", ["one", "a"])
        graphql_context.instance.delete_dynamic_partition("dynamic", "a")

        repository_selector = infer_repository_selector(graphql_context)
        with (
            mock.patch.object(
                type(graphql_context.instance),
                "supports_wipe_on_delete_for_multipartitioned_assets",
                new_callable=mock.PropertyMock,
                return_value=True,
            ),
            mock.patch.object(
                graphql_context.instance, "wipe_asset_partitions"
            ) as mock_wipe_asset_partitions,
        ):
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "dynamic",
                    "partitionKeys": ["a"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert (
            result.data["deleteDynamicPartitions"]["__typename"] == "DeleteDynamicPartitionsSuccess"
        ), str(result.data)

        # the deleted key is still expanded, and always into the dynamic dimension's slot,
        # so "one|a" is untouched
        wiped = {
            (call.args[0], tuple(sorted(call.args[1])))
            for call in mock_wipe_asset_partitions.call_args_list
        }
        assert wiped == {
            (AssetKey("dynamic_in_multipartitions_success"), ("a|a", "a|b", "a|c")),
            (AssetKey("dynamic_in_multipartitions_fail"), ("a|a", "a|b", "a|c")),
        }
        assert not any("one|a" in keys for _, keys in wiped)
        assert set(graphql_context.instance.get_dynamic_partitions("dynamic")) == {"one"}

    def test_delete_dynamic_partitions_wipe_without_wipe_permission(self, graphql_context):
        graphql_context.instance.add_dynamic_partitions("foo", ["bar", "baz"])

        repository_selector = infer_repository_selector(graphql_context)
        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph",
                side_effect=UserFacingGraphQLError(GrapheneUnauthorizedError()),
            ),
            mock.patch.object(
                graphql_context.instance, "wipe_asset_partitions"
            ) as mock_wipe_asset_partitions,
        ):
            result = execute_dagster_graphql(
                graphql_context,
                DELETE_DYNAMIC_PARTITIONS_MUTATION,
                variables={
                    "partitionsDefName": "foo",
                    "partitionKeys": ["bar"],
                    "repositorySelector": repository_selector,
                    "wipeMaterializations": True,
                },
            )
        assert not result.errors
        assert result.data["deleteDynamicPartitions"]["__typename"] == "UnauthorizedError", str(
            result.data
        )

        # neither the wipe nor the deletion happened
        mock_wipe_asset_partitions.assert_not_called()
        assert set(graphql_context.instance.get_dynamic_partitions("foo")) == {"bar", "baz"}

    def test_nonexistent_dynamic_partitions_def_throws_error(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            ADD_DYNAMIC_PARTITION_MUTATION,
            variables={
                "partitionsDefName": "nonexistent",
                "partitionKey": "bar",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["addDynamicPartition"]["__typename"] == "UnauthorizedError"
        # If the selected repository does not contain a matching dynamic partitions definition
        # we should throw an unauthorized error
        assert (
            "does not contain a dynamic partitions definition"
            in result.data["addDynamicPartition"]["message"]
        )


class TestDynamicPartitionReadonlyFailure(ReadonlyGraphQLContextTestMatrix):
    def test_unauthorized_error_on_add_dynamic_partitions(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            ADD_DYNAMIC_PARTITION_MUTATION,
            variables={
                "partitionsDefName": "foo",
                "partitionKey": "bar",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["addDynamicPartition"]["__typename"] == "UnauthorizedError"

    def test_unauthorized_error_on_delete_dynamic_partitions(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            DELETE_DYNAMIC_PARTITIONS_MUTATION,
            variables={
                "partitionsDefName": "foo",
                "partitionKeys": ["bar"],
                "repositorySelector": repository_selector,
                "wipeMaterializations": True,
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["deleteDynamicPartitions"]["__typename"] == "UnauthorizedError"


def _mock_graphene_info(
    supports_multipartitioned_wipe: bool = False,
    dynamic_partitions: Mapping[str, Sequence[str]] | None = None,
):
    """A graphene_info whose instance is a mocked DagsterInstance.

    dynamic_partitions is what the instance returns from get_dynamic_partitions, keyed by
    partitions definition name. A dynamic dimension's keys are stored in the database rather
    than in the definition, so this is only needed when the other dimension is dynamic.
    """
    graphene_info = mock.MagicMock()
    # spec'd so the instance still satisfies the DynamicPartitionsStore protocol, which
    # expanding a multi-partitioned asset's dimension keys requires
    graphene_info.context.instance = mock.MagicMock(spec=DagsterInstance)
    graphene_info.context.instance.supports_wipe_on_delete_for_multipartitioned_assets = (
        supports_multipartitioned_wipe
    )
    graphene_info.context.instance.get_dynamic_partitions.side_effect = lambda partitions_def_name: (
        (dynamic_partitions or {})[partitions_def_name]
    )
    return graphene_info


TARGET_DYNAMIC_DEF = DynamicPartitionsSnap(name="foo")
UNRELATED_DYNAMIC_DEF = DynamicPartitionsSnap(name="other")
STATIC_DEF = StaticPartitionsSnap(partition_keys=["x", "y"])
EMPTY_STATIC_DEF = StaticPartitionsSnap(partition_keys=[])


def _multipartitions_snap(**dimensions: PartitionsSnap) -> MultiPartitionsSnap:
    """A multi-partitions snap from dimension name to that dimension's partitions.

    Dimensions are ordered by name, so the dimension named "first" holds the leading key of a
    stored multi-partition key and "second" holds the trailing one.
    """
    return MultiPartitionsSnap(
        partition_dimensions=[
            PartitionDimensionSnap(name=name, partitions=partitions)
            for name, partitions in dimensions.items()
        ]
    )


DYNAMIC_FIRST_SNAP = _multipartitions_snap(first=TARGET_DYNAMIC_DEF, second=STATIC_DEF)
DYNAMIC_SECOND_SNAP = _multipartitions_snap(first=STATIC_DEF, second=TARGET_DYNAMIC_DEF)
DYNAMIC_OTHER_DIMENSION_SNAP = _multipartitions_snap(
    first=TARGET_DYNAMIC_DEF, second=UNRELATED_DYNAMIC_DEF
)
BOTH_DIMENSIONS_SNAP = _multipartitions_snap(first=TARGET_DYNAMIC_DEF, second=TARGET_DYNAMIC_DEF)


def _multi_target(partitions_snap: MultiPartitionsSnap) -> MultipartitionedAssetWipeTarget:
    """A wipe target for whichever of the snap's dimensions uses TARGET_DYNAMIC_DEF."""
    dimension_name = next(
        dimension.name
        for dimension in partitions_snap.partition_dimensions
        if dimension.partitions == TARGET_DYNAMIC_DEF
    )
    return MultipartitionedAssetWipeTarget(
        asset_key=AssetKey("multi_asset"),
        dimension_name=dimension_name,
        partitions_snap=partitions_snap,
    )


def _mock_graphene_info_with_asset(asset_key: AssetKey, partitions_snap) -> mock.MagicMock:
    graphene_info = mock.MagicMock()
    graphene_info.context.has_code_location.return_value = True
    code_location = graphene_info.context.get_code_location.return_value
    code_location.has_repository.return_value = True
    asset_node_snap = mock.MagicMock()
    asset_node_snap.asset_key = asset_key
    asset_node_snap.partitions = partitions_snap
    code_location.get_repository.return_value.repository_snap.asset_nodes = [asset_node_snap]
    return graphene_info


@pytest.mark.parametrize(
    "partitions_snap,expected",
    [
        pytest.param(
            DYNAMIC_FIRST_SNAP,
            ["first"],
            id="dynamic_dimension_first",
        ),
        pytest.param(
            DYNAMIC_SECOND_SNAP,
            ["second"],
            id="dynamic_dimension_last",
        ),
        # one asset can use the same dynamic def for more than one dimension
        pytest.param(
            BOTH_DIMENSIONS_SNAP,
            ["first", "second"],
            id="same_dynamic_def_in_two_dimensions",
        ),
        # a dimension using a different dynamic def is not a wipe target
        pytest.param(
            _multipartitions_snap(first=UNRELATED_DYNAMIC_DEF, second=TARGET_DYNAMIC_DEF),
            ["second"],
            id="unrelated_dynamic_def",
        ),
    ],
)
def test_multipartitioned_wipe_target_dimensions(partitions_snap, expected):
    asset_key = AssetKey("multi_asset")
    graphene_info = _mock_graphene_info_with_asset(asset_key, partitions_snap)

    direct_asset_keys, multi_targets = _get_asset_keys_using_dynamic_partitions_def(
        graphene_info,
        RepositorySelector(location_name="location", repository_name="repo"),
        "foo",
    )

    assert direct_asset_keys == []
    assert [target.dimension_name for target in multi_targets] == expected
    assert all(target.asset_key == asset_key for target in multi_targets)


class TestWipeMaterializationsForDeletedPartitions:
    def test_wipes_every_directly_partitioned_asset(self):
        graphene_info = _mock_graphene_info()
        direct_asset_keys = [AssetKey("asset_one"), AssetKey("asset_two")]

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ) as mock_assert_permission:
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar", "baz"],
                direct_asset_keys=direct_asset_keys,
                multi_targets=[],
            )

        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("asset_one"), ["bar", "baz"]),
            mock.call(AssetKey("asset_two"), ["bar", "baz"]),
        ]
        # the permission check covers every affected asset
        assert mock_assert_permission.call_args.args[2] == direct_asset_keys

    def test_multipartitioned_assets_unsupported(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=False)

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ) as mock_assert_permission,
            pytest.raises(UserFacingGraphQLError) as exc_info,
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[AssetKey("asset_one")],
                multi_targets=[_multi_target(DYNAMIC_FIRST_SNAP)],
            )

        assert exc_info.value.error.__class__.__name__ == "GrapheneUnsupportedOperationError"
        assert "multi_asset" in exc_info.value.error.message
        graphene_info.context.instance.wipe_asset_partitions.assert_not_called()
        # multi-partitioned assets are included in the permission check even though
        # wiping them is rejected, so the next branch only swaps the rejection
        assert mock_assert_permission.call_args.args[2] == [
            AssetKey("asset_one"),
            AssetKey("multi_asset"),
        ]

    def test_multipartitioned_assets_wiped_when_supported(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ) as mock_assert_permission:
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar", "baz"],
                direct_asset_keys=[AssetKey("asset_one")],
                multi_targets=[_multi_target(DYNAMIC_FIRST_SNAP)],
            )

        # each deleted dimension key expands into one key per key of the other dimension
        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("asset_one"), ["bar", "baz"]),
            mock.call(AssetKey("multi_asset"), ["bar|x", "bar|y", "baz|x", "baz|y"]),
        ]
        assert mock_assert_permission.call_args.args[2] == [
            AssetKey("asset_one"),
            AssetKey("multi_asset"),
        ]

    def test_multipartitioned_assets_wiped_when_dynamic_dimension_sorts_last(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)
        target = _multi_target(DYNAMIC_SECOND_SNAP)

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[target],
            )

        # the deleted key lands in the second component, since dimensions are ordered by name
        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("multi_asset"), ["x|bar", "y|bar"]),
        ]

    def test_multipartitioned_asset_with_empty_other_dimension_is_skipped(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)
        empty_snap = _multipartitions_snap(first=TARGET_DYNAMIC_DEF, second=EMPTY_STATIC_DEF)

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[_multi_target(empty_snap)],
            )

        graphene_info.context.instance.wipe_asset_partitions.assert_not_called()

    def test_multipartitioned_asset_with_dynamic_other_dimension(self):
        # the other dimension's keys have to be read from the instance, which only works
        # inside a partition loading context
        graphene_info = _mock_graphene_info(
            supports_multipartitioned_wipe=True, dynamic_partitions={"other": ["p", "q"]}
        )

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[_multi_target(DYNAMIC_OTHER_DIMENSION_SNAP)],
            )

        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("multi_asset"), ["bar|p", "bar|q"]),
        ]

    def test_asset_using_the_same_dynamic_def_for_both_dimensions(self):
        # both dimensions match, so the asset yields two targets whose expansions overlap on
        # "bar|bar"; the two are merged into a single deduplicated wipe
        graphene_info = _mock_graphene_info(
            supports_multipartitioned_wipe=True, dynamic_partitions={"foo": ["bar", "baz"]}
        )
        targets = [
            MultipartitionedAssetWipeTarget(
                asset_key=AssetKey("multi_asset"),
                dimension_name=dimension_name,
                partitions_snap=BOTH_DIMENSIONS_SNAP,
            )
            for dimension_name in ("first", "second")
        ]

        with mock.patch(
            "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
        ) as mock_assert_permission:
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=targets,
            )

        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("multi_asset"), ["bar|bar", "bar|baz", "baz|bar"]),
        ]
        assert mock_assert_permission.call_args.args[2] == [AssetKey("multi_asset")]

    def test_unsupported_storage(self):
        graphene_info = _mock_graphene_info()
        graphene_info.context.instance.wipe_asset_partitions.side_effect = NotImplementedError

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ),
            pytest.raises(UserFacingGraphQLError) as exc_info,
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[AssetKey("asset_one")],
                multi_targets=[],
            )

        assert exc_info.value.error.__class__.__name__ == "GrapheneUnsupportedOperationError"
        assert "not supported by this event log storage" in exc_info.value.error.message

    def test_unsupported_storage_for_multipartitioned_asset(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)
        graphene_info.context.instance.wipe_asset_partitions.side_effect = NotImplementedError

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ),
            pytest.raises(UserFacingGraphQLError) as exc_info,
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[_multi_target(DYNAMIC_FIRST_SNAP)],
            )

        assert exc_info.value.error.__class__.__name__ == "GrapheneUnsupportedOperationError"
        assert "not supported by this event log storage" in exc_info.value.error.message

    def test_rejects_expansion_over_the_limit(self):
        # one deleted key against a two-key other dimension already exceeds a limit of one
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ),
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.MAX_WIPE_ASSET_PARTITIONS",
                1,
            ),
            pytest.raises(UserFacingGraphQLError) as exc_info,
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[_multi_target(DYNAMIC_FIRST_SNAP)],
            )

        assert exc_info.value.error.__class__.__name__ == "GrapheneUnsupportedOperationError"
        assert "over the limit of 1" in exc_info.value.error.message
        # the projection is checked before anything is wiped
        graphene_info.context.instance.wipe_asset_partitions.assert_not_called()

    def test_expansion_under_the_limit_is_allowed(self):
        graphene_info = _mock_graphene_info(supports_multipartitioned_wipe=True)

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ),
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.MAX_WIPE_ASSET_PARTITIONS",
                2,
            ),
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[],
                multi_targets=[_multi_target(DYNAMIC_FIRST_SNAP)],
            )

        assert graphene_info.context.instance.wipe_asset_partitions.call_args_list == [
            mock.call(AssetKey("multi_asset"), ["bar|x", "bar|y"]),
        ]

    def test_other_dimension_is_read_once_regardless_of_deleted_key_count(self):
        """Expanding must not re-read the other dimension per deleted key -- when that dimension
        is dynamic each read is a database query, and when it is a time window each one rebuilds
        the whole key list.
        """
        call_counts = []
        for num_deleted_keys in (1, 50):
            graphene_info = _mock_graphene_info(
                supports_multipartitioned_wipe=True, dynamic_partitions={"other": ["p", "q"]}
            )
            with mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph"
            ):
                wipe_materializations_for_deleted_partitions(
                    graphene_info,
                    partitions_def_name="foo",
                    partition_keys=[f"key_{i}" for i in range(num_deleted_keys)],
                    direct_asset_keys=[],
                    multi_targets=[_multi_target(DYNAMIC_OTHER_DIMENSION_SNAP)],
                )
            call_counts.append(graphene_info.context.instance.get_dynamic_partitions.call_count)

        assert call_counts[0] == call_counts[1]

    def test_permission_failure_prevents_wipe(self):
        graphene_info = _mock_graphene_info()

        with (
            mock.patch(
                "dagster_graphql.implementation.execution.dynamic_partitions.assert_permission_for_asset_graph",
                side_effect=UserFacingGraphQLError(GrapheneUnauthorizedError()),
            ),
            pytest.raises(UserFacingGraphQLError) as exc_info,
        ):
            wipe_materializations_for_deleted_partitions(
                graphene_info,
                partitions_def_name="foo",
                partition_keys=["bar"],
                direct_asset_keys=[AssetKey("asset_one")],
                multi_targets=[],
            )

        assert exc_info.value.error.__class__.__name__ == "GrapheneUnauthorizedError"
        graphene_info.context.instance.wipe_asset_partitions.assert_not_called()
