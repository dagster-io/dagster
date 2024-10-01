from collections import OrderedDict

from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
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
mutation($partitionsDefName: String!, $partitionKeys: [String!]!, $repositorySelector: RepositorySelector!) {
    deleteDynamicPartitions(partitionsDefName: $partitionsDefName, partitionKeys: $partitionKeys, repositorySelector: $repositorySelector) {
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
