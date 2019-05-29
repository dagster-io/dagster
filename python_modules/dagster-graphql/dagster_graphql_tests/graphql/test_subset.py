from dagster_graphql.test.utils import execute_dagster_graphql
from .setup import define_context

PIPELINE_OR_ERROR_SUBSET_QUERY = '''
query PipelineQuery($name: String! $solidSubset: [String!])
{
    pipelineOrError(params: { name: $name, solidSubset: $solidSubset }) {
        __typename
        ... on Pipeline {
            name
            solids {
                name
            }
            configTypes {
                __typename
                name
                ... on CompositeConfigType {
                    fields {
                    name
                    configType {
                        name
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        }
        ... on SolidNotFoundError {
            solidName
        }
    }
}
'''
PIPELINE_SUBSET_QUERY = '''
query PipelineQuery($name: String! $solidSubset: [String!])
{
    pipeline(params: { name: $name, solidSubset: $solidSubset }) {
        name
        solids {
            name
        }
        configTypes {
          __typename
          name
          ... on CompositeConfigType {
            fields {
              name
              configType {
                name
                __typename
              }
              __typename
            }
            __typename
          }
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


def do_test_subset(query, top_key):
    subset_result = execute_dagster_graphql(
        define_context(), query, {'name': 'csv_hello_world', 'solidSubset': ['sum_sq_solid']}
    )

    assert not subset_result.errors
    assert subset_result.data

    assert [solid_data['name'] for solid_data in subset_result.data[top_key]['solids']] == [
        'sum_sq_solid'
    ]

    subset_types_dict = types_dict_of_result(subset_result, top_key)
    assert field_names_of(subset_types_dict, 'CsvHelloWorld.SumSqSolid.Inputs') == {'sum_df'}
    assert 'CsvHelloWorld.SumSolid.Inputs' not in subset_types_dict

    full_types_dict = types_dict_of_result(
        execute_dagster_graphql(define_context(), query, {'name': 'csv_hello_world'}), top_key
    )

    assert 'CsvHelloWorld.SumSolid.Inputs' in full_types_dict
    assert 'CsvHelloWorld.SumSqSolid.Inputs' not in full_types_dict

    assert field_names_of(full_types_dict, 'CsvHelloWorld.SumSolid.Inputs') == {'num'}


def test_csv_hello_world_pipeline_subset():
    do_test_subset(PIPELINE_SUBSET_QUERY, 'pipeline')


def test_csv_hello_world_pipeline_or_error_subset():
    do_test_subset(PIPELINE_OR_ERROR_SUBSET_QUERY, 'pipelineOrError')


def test_csv_hello_world_pipeline_or_error_subset_wrong_solid_name():
    result = execute_dagster_graphql(
        define_context(),
        PIPELINE_OR_ERROR_SUBSET_QUERY,
        {'name': 'csv_hello_world', 'solidSubset': ['nope']},
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'SolidNotFoundError'
    assert result.data['pipelineOrError']['solidName'] == 'nope'
