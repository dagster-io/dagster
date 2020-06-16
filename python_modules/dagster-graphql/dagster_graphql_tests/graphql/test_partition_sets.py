from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix

GET_PARTITION_SETS_FOR_PIPELINE_QUERY = '''
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
'''

GET_PARTITION_SET_QUERY = '''
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
                partitions {
                    results {
                        name
                    }
                }
            }
        }
    }
'''


class TestPartitionSets(ReadonlyGraphQLContextTestMatrix):
    def test_get_partition_sets_for_pipeline(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={'repositorySelector': selector, 'pipelineName': 'no_config_pipeline'},
        )

        assert result.data
        snapshot.assert_match(result.data)

        invalid_pipeline_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
            variables={'repositorySelector': selector, 'pipelineName': 'invalid_pipeline'},
        )

        assert invalid_pipeline_result.data
        snapshot.assert_match(invalid_pipeline_result.data)

    def test_get_partition_set(self, graphql_context, snapshot):
        selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={'partitionSetName': 'integer_partition', 'repositorySelector': selector},
        )

        assert result.data
        snapshot.assert_match(result.data)

        invalid_partition_set_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_SET_QUERY,
            variables={'partitionSetName': 'invalid_partition', 'repositorySelector': selector},
        )

        print(invalid_partition_set_result.data)
        assert (
            invalid_partition_set_result.data['partitionSetOrError']['__typename']
            == 'PartitionSetNotFoundError'
        )
        assert invalid_partition_set_result.data

        snapshot.assert_match(invalid_partition_set_result.data)
