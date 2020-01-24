from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster.utils import file_relative_path

GET_PARTITION_SETS_QUERY = '''
{
    partitionSetsOrError {
        __typename
        ...on PartitionSets {
            results {
                name
                pipelineName
                solidSubset
                mode
            }
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
                    solidSubset
                    mode
                }
            }
            ...on PipelineNotFoundError {
                message
            }
        }
    }
'''

GET_PARTITION_SET_QUERY = '''
    query ParitionSetQuery($partitionSetName: String!) {
        partitionSetOrError(partitionSetName: $partitionSetName) {
            __typename
            ...on PartitionSet {
                name
                pipelineName
                solidSubset
                mode
                partitions {
                    name
                }
            }
        }
    }
'''


def test_get_all_partition_sets(snapshot):
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml')
    )

    result = execute_dagster_graphql(context, GET_PARTITION_SETS_QUERY)

    assert result.data
    snapshot.assert_match(result.data)


def test_get_partition_sets_for_pipeline(snapshot):
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml')
    )

    result = execute_dagster_graphql(
        context,
        GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
        variables={'pipelineName': 'no_config_pipeline'},
    )

    assert result.data
    snapshot.assert_match(result.data)

    invalid_pipeline_result = execute_dagster_graphql(
        context,
        GET_PARTITION_SETS_FOR_PIPELINE_QUERY,
        variables={'pipelineName': 'invalid_pipeline'},
    )

    assert invalid_pipeline_result.data
    snapshot.assert_match(invalid_pipeline_result.data)


def test_get_partition_set(snapshot):
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml')
    )

    result = execute_dagster_graphql(
        context, GET_PARTITION_SET_QUERY, variables={'partitionSetName': 'integer_partition'},
    )

    assert result.data
    snapshot.assert_match(result.data)

    invalid_partition_set_result = execute_dagster_graphql(
        context, GET_PARTITION_SET_QUERY, variables={'partitionSetName': 'invalid_partition'},
    )

    assert invalid_partition_set_result.data
    snapshot.assert_match(invalid_partition_set_result.data)
