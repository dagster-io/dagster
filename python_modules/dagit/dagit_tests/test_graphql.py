from graphql import graphql

from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    SolidDefinition,
    check,
    lambda_solid,
    types,
)
import dagster.pandas as dagster_pd

from dagit.schema import create_schema
from dagit.app import RepositoryContainer

from .production_query import PRODUCTION_QUERY


@lambda_solid(
    inputs=[InputDefinition('num', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum']**2
    return sum_sq_df


def define_pipeline_one():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
            sum_sq_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'sum_sq_solid': {
                'sum_df': DependencyDefinition(sum_solid.name),
            },
        },
    )


def define_pipeline_two():
    return PipelineDefinition(
        name='pandas_hello_world_two',
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
        },
    )


def define_more_complicated_config():
    return PipelineDefinition(
        name='more_complicated_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_config',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_def=ConfigDefinition(
                    types.ConfigDictionary(
                        'SomeSolidWithConfig',
                        {
                            'field_one':
                            types.Field(types.String),
                            'field_two':
                            types.Field(types.String, is_optional=True),
                            'field_three':
                            types.Field(
                                types.String,
                                is_optional=True,
                                default_value='some_value',
                            )
                        },
                    )
                )
            )
        ]
    )


CONFIG_VALIDATION_QUERY = '''
query PipelineQuery($config: GenericScalar)
{
    isPipelineConfigValid(pipelineName: "pandas_hello_world", config: $config) {
        __typename
        ... on PipelineConfigValidationValid {
            pipeline { name }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors {
                errorData {
                    __typename
                    ... on RuntimeMismatchErrorData {
                        type { name } 
                        valueRep 
                    }
                }
                message
                reason
                stack {
                    entries {
                        field { 
                            name
                            type { 
                                name
                            }
                        }
                    }
                }
            }
        }
    }
}
'''


def test_basic_valid_config():
    result = execute_dagster_graphql(
        define_repo(),
        CONFIG_VALIDATION_QUERY,
        {
            'config': {
                'solids': {
                    'load_num_csv': {
                        'config': {
                            'path': 'pandas_hello_world/num.csv',
                        },
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'


def field_stack(error_data):
    return [entry['field']['name'] for entry in error_data['stack']['entries']]


def test_basic_invalid_config():
    result = execute_dagster_graphql(
        define_repo(),
        CONFIG_VALIDATION_QUERY,
        {
            'config': {
                'solids': {
                    'load_num_csv': {
                        'config': {
                            'path': 123,
                        },
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    error_data = result.data['isPipelineConfigValid']['errors'][0]
    assert error_data['message']
    assert error_data['stack']
    assert error_data['stack']['entries']
    assert error_data['reason'] == 'RUNTIME_TYPE_MISMATCH'

    assert ['solids', 'load_num_csv', 'config', 'path'] == field_stack(error_data)


def define_repo():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'pandas_hello_world': define_pipeline_one,
            'pandas_hello_world_two': define_pipeline_two,
            'more_complicated_config': define_more_complicated_config,
        }
    )


def execute_dagster_graphql(repo, query, variables=None):
    return graphql(
        create_schema(),
        query,
        context={'repository_container': RepositoryContainer(repository=repo)},
        variables=variables,
    )


def test_pipelines():
    result = execute_dagster_graphql(define_repo(), '{ pipelines { name } }')
    assert result.data
    assert not result.errors

    assert set([p['name'] for p in result.data['pipelines']]) == set(
        [
            'pandas_hello_world',
            'pandas_hello_world_two',
            'more_complicated_config',
        ]
    )


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_repo(),
        '''
    {
        pipeline(name: "pandas_hello_world_two") {
            name
        }
    }''',
    )

    assert result.data
    assert not result.errors
    assert result.data['pipeline']['name'] == 'pandas_hello_world_two'


COMPUTE_NODE_QUERY = '''
query PipelineQuery($config: GenericScalar)
{
  pipeline(name:"pandas_hello_world") {
    name
    executionPlan(config:$config) {
      pipeline {
        name
      }
      steps {
        name
        solid {
            name
        }
        tag
        inputs {
           name
           type {
               name
           }
           dependsOn {
               name
           }
        }
        outputs {
            name
            type {
                name
            }
        }
      }
    }
  }
}
'''


def test_query_execution_plan_snapshot(snapshot):
    result = execute_dagster_graphql(
        define_repo(),
        COMPUTE_NODE_QUERY,
        {
            'config': {
                'solids': {
                    'load_num_csv': {
                        'config': {
                            'path': 'pandas_hello_world/num.csv',
                        },
                    },
                },
            },
        },
    )

    assert result.data
    assert not result.errors

    snapshot.assert_match(result.data)


def test_query_execution_plan():
    result = execute_dagster_graphql(
        define_repo(),
        COMPUTE_NODE_QUERY,
        {
            'config': {
                'solids': {
                    'load_num_csv': {
                        'config': {
                            'path': 'pandas_hello_world/num.csv',
                        },
                    },
                },
            },
        },
    )

    if result.errors:
        raise Exception(result.errors[0])

    assert result.data
    assert not result.errors

    plan_data = result.data['pipeline']['executionPlan']

    names = get_nameset(plan_data['steps'])
    assert len(names) == 3

    assert names == set(['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform'])

    assert result.data['pipeline']['executionPlan']['pipeline']['name'] == 'pandas_hello_world'

    cn = get_named_thing(plan_data['steps'], 'sum_solid.transform')

    assert cn['tag'] == 'TRANSFORM'
    assert cn['solid']['name'] == 'sum_solid'

    assert get_nameset(cn['inputs']) == set(['num'])

    sst_input = get_named_thing(cn['inputs'], 'num')
    assert sst_input['type']['name'] == 'PandasDataFrame'

    assert sst_input['dependsOn']['name'] == 'load_num_csv.transform'

    sst_output = get_named_thing(cn['outputs'], 'result')
    assert sst_output['type']['name'] == 'PandasDataFrame'


def get_nameset(llist):
    return set([item['name'] for item in llist])


def get_named_thing(llist, name):
    for cn in llist:
        if cn['name'] == name:
            return cn

    check.failed('not found')


def test_production_query():
    result = execute_dagster_graphql(
        define_repo(),
        PRODUCTION_QUERY,
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data
    assert not result.errors
