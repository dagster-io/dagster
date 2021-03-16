from collections import OrderedDict

from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_repository_selector,
)

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
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

GET_PARTITION_SET_RUNS_QUERY = """
    query PartitionSetQuery($repositorySelector: RepositorySelector!, $partitionSetName: String!) {
        partitionSetOrError(repositorySelector: $repositorySelector, partitionSetName: $partitionSetName) {
            ...on PartitionSet {
                partitionsOrError {
                    ... on Partitions {
                        results {
                            name
                            runs {
                                runId
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
                    ... on PartitionStatuses {
                        results {
                            id
                            partitionName
                            runStatus
                        }
                    }
                }
            }
        }
    }
"""


class TestPartitionSets(ReadonlyGraphQLContextTestMatrix):
    def test_get_partition_sets_for_pipeline(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={"repositorySelector": selector, "pipelineName": "no_config_pipeline"},
        )

        assert result.data
        snapshot.assert_match(result.data)

        invalid_pipeline_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={"repositorySelector": selector, "pipelineName": "invalid_pipeline"},
        )

        assert invalid_pipeline_result.data
        snapshot.assert_match(invalid_pipeline_result.data)

    def test_get_partition_set(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={"partitionSetName": "integer_partition", "repositorySelector": selector},
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

    def test_get_partition_tags(self, graphql_context):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_TAGS_QUERY,
            variables={"partitionSetName": "integer_partition", "repositorySelector": selector},
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
            "dagster/partition_set": "integer_partition",
        }


class TestPartitionSetRuns(ExecutingGraphQLContextTestMatrix):
    def test_get_partition_runs(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integer_partition",
                    },
                    "partitionNames": ["2", "3"],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data["launchPartitionBackfill"]["__typename"] == "LaunchBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2
        run_ids = result.data["launchPartitionBackfill"]["launchedRunIds"]

        result = execute_dagster_graphql(
            graphql_context,
            query=GET_PARTITION_SET_RUNS_QUERY,
            variables={
                "partitionSetName": "integer_partition",
                "repositorySelector": repository_selector,
            },
        )
        assert not result.errors
        assert result.data
        partitions = result.data["partitionSetOrError"]["partitionsOrError"]["results"]
        assert len(partitions) == 10
        for partition in partitions:
            if partition["name"] not in ("2", "3"):
                assert len(partition["runs"]) == 0
            else:
                assert len(partition["runs"]) == 1
                assert partition["runs"][0]["runId"] in run_ids

    def test_get_partition_status(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integer_partition",
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
                "partitionSetName": "integer_partition",
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
                        "partitionSetName": "integer_partition",
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
                "partitionSetName": "integer_partition",
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
