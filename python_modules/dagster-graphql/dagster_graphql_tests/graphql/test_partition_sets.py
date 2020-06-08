from dagster_graphql.test.utils import execute_dagster_graphql

GET_PARTITION_SETS_QUERY = '''
{
    partitionSetsOrError {
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
    }
}
'''

GET_PARTITION_SETS_FOR_PIPELINE_QUERY = '''
    query PartitionSetsQuery($pipelineName: String!) {
        partitionSetsOrError(pipelineName: $pipelineName) {
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
    query PartitionSetQuery($partitionSetName: String!) {
        partitionSetOrError(partitionSetName: $partitionSetName) {
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


def test_get_all_partition_sets(graphql_context, snapshot):
    result = execute_dagster_graphql(graphql_context, GET_PARTITION_SETS_QUERY)
    assert result.data
    snapshot.assert_match(result.data)


def test_get_partition_sets_for_pipeline(graphql_context, snapshot):
    result = execute_dagster_graphql(
        graphql_context,
        GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
        variables={'pipelineName': 'no_config_pipeline'},
    )

    assert result.data
    snapshot.assert_match(result.data)

    invalid_pipeline_result = execute_dagster_graphql(
        graphql_context,
        GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
        variables={'pipelineName': 'invalid_pipeline'},
    )

    assert invalid_pipeline_result.data
    snapshot.assert_match(invalid_pipeline_result.data)


def test_get_partition_set(graphql_context, snapshot):
    result = execute_dagster_graphql(
        graphql_context,
        GET_PARTITION_SET_QUERY,
        variables={'partitionSetName': 'integer_partition'},
    )

    assert result.data
    snapshot.assert_match(result.data)

    invalid_partition_set_result = execute_dagster_graphql(
        graphql_context,
        GET_PARTITION_SET_QUERY,
        variables={'partitionSetName': 'invalid_partition'},
    )

    print(invalid_partition_set_result.data)
    assert (
        invalid_partition_set_result.data['partitionSetOrError']['__typename']
        == 'PartitionSetNotFoundError'
    )
    assert invalid_partition_set_result.data

    snapshot.assert_match(invalid_partition_set_result.data)
