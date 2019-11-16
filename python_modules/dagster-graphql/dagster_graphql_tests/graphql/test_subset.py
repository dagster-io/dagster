from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_context

SCHEMA_OR_ERROR_SUBSET_QUERY = '''
query EnvironmentQuery($pipelineName: String!, $solidSubset: [String!]){
    environmentSchemaOrError(selector :{ name: $pipelineName, solidSubset: $solidSubset}) {
        __typename
        ... on EnvironmentSchema {
            allConfigTypes {
                __typename
                name
                ... on CompositeConfigType {
                    __typename
                    fields {
                        __typename
                        name
                        configType {
                            name
                            __typename
                        }
                    }
                }
            }
        }
        ... on InvalidSubsetError {
            message
        }
    }
}
'''


def field_names_of(type_dict, typename):
    return {field_data['name'] for field_data in type_dict[typename]['fields']}


def types_dict_of_result(subset_result, top_key):
    return {
        type_data['name']: type_data for type_data in subset_result.data[top_key]['configTypes']
    }


def test_csv_hello_world_pipeline_or_error_subset():
    subset_result = execute_dagster_graphql(
        define_context(),
        SCHEMA_OR_ERROR_SUBSET_QUERY,
        {'pipelineName': 'csv_hello_world', 'solidSubset': ['sum_sq_solid']},
    )

    assert not subset_result.errors
    assert subset_result.data

    subset_types_dict = {
        type_data['name']: type_data
        for type_data in subset_result.data['environmentSchemaOrError']['allConfigTypes']
    }

    assert field_names_of(subset_types_dict, 'CsvHelloWorld.SumSqSolid.Inputs') == {'sum_df'}
    assert 'CsvHelloWorld.SumSolid.Inputs' not in subset_types_dict

    full_result = execute_dagster_graphql(
        define_context(), SCHEMA_OR_ERROR_SUBSET_QUERY, {'pipelineName': 'csv_hello_world'}
    )
    full_types_dict = {
        type_data['name']: type_data
        for type_data in full_result.data['environmentSchemaOrError']['allConfigTypes']
    }

    assert 'CsvHelloWorld.SumSolid.Inputs' in full_types_dict
    assert 'CsvHelloWorld.SumSqSolid.Inputs' not in full_types_dict

    assert field_names_of(full_types_dict, 'CsvHelloWorld.SumSolid.Inputs') == {'num'}


def test_csv_hello_world_pipeline_or_error_subset_wrong_solid_name():
    result = execute_dagster_graphql(
        define_context(),
        SCHEMA_OR_ERROR_SUBSET_QUERY,
        {'pipelineName': 'csv_hello_world', 'solidSubset': ['nope']},
    )

    assert not result.errors
    assert result.data
    assert result.data['environmentSchemaOrError']['__typename'] == 'InvalidSubsetError'
    assert '"nope" does not exist' in result.data['environmentSchemaOrError']['message']
