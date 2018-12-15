import uuid

from graphql import (
    graphql,
    parse,
)

from dagster import (
    DependencyDefinition,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    ResourceDefinition,
    SolidDefinition,
    check,
    lambda_solid,
    types,
)
from dagster.utils import script_relative_path

import dagster_contrib.pandas as dagster_pd

from dagit.app import RepositoryContainer
from dagit.pipeline_execution_manager import SynchronousExecutionManager
from dagit.pipeline_run_storage import PipelineRunStorage
from dagit.schema import create_schema
from dagit.schema.context import DagsterGraphQLContext

from dagit.dagit_tests.production_query import PRODUCTION_QUERY


def define_repository():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'context_config_pipeline': define_context_config_pipeline,
            'more_complicated_config': define_more_complicated_config,
            'more_complicated_nested_config': define_more_complicated_nested_config,
            'pandas_hello_world': define_pipeline_one,
            'pandas_hello_world_two': define_pipeline_two,
            'pipeline_with_list': define_pipeline_with_list,
        },
    )


def define_context():
    return DagsterGraphQLContext(
        RepositoryContainer(repository=define_repository()),
        PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )


def execute_dagster_graphql(context, query, variables=None):
    return graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        # executor=GeventObservableExecutor(),
        allow_subscriptions=True,
        return_promise=False
    )


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


def define_pipeline_with_list():
    return PipelineDefinition(
        name='pipeline_with_list',
        solids=[
            SolidDefinition(
                name='solid_with_list',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=Field(types.List(types.Int)),
            ),
        ],
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
                config_field=types.Field(
                    types.Dict(
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
                    ),
                )
            ),
        ],
    )


CONFIG_VALIDATION_QUERY = '''
query PipelineQuery($executionParams: PipelineExecutionParams!)
{
    isPipelineConfigValid(executionParams: $executionParams) {
        __typename
        ... on PipelineConfigValidationValid {
            pipeline { name }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors {
                __typename
                ... on RuntimeMismatchConfigError {
                    type { name }
                    valueRep
                }
                ... on MissingFieldConfigError {
                    field { name }
                }
                ... on FieldNotDefinedConfigError {
                    fieldName
                }
                ... on SelectorTypeConfigError {
                    incomingFields
                }
                message
                reason
                stack {
                    entries {
                        __typename
                        ... on EvaluationStackPathEntry {
                            field {
                                name
                                type {
                                    name
                                }
                            }
                        }
                        ... on EvaluationStackListItemEntry {
                            listIndex
                        }
                    }
                }
            }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def execute_config_graphql(pipeline_name, config):
    return execute_dagster_graphql(
        define_context(),
        CONFIG_VALIDATION_QUERY,
        {
            'executionParams': {
                'pipelineName': pipeline_name,
                'config': config,
            },
        },
    )


def test_pipeline_not_found():
    result = execute_config_graphql(
        pipeline_name='nope',
        config={},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineNotFoundError'
    assert result.data['isPipelineConfigValid']['pipelineName'] == 'nope'


def test_basic_valid_config():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config={
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': 'pandas_hello_world/num.csv',
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'


def test_root_field_not_defined():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config={
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': 'pandas_hello_world/num.csv',
                    },
                },
            },
            'nope': {},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    errors = result.data['isPipelineConfigValid']['errors']
    assert len(errors) == 1
    error = errors[0]
    assert error['__typename'] == 'FieldNotDefinedConfigError'
    assert error['fieldName'] == 'nope'
    assert not error['stack']['entries']


def test_root_wrong_type():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config=123,
    )
    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'pandas_hello_world'
    errors = result.data['isPipelineConfigValid']['errors']
    assert len(errors) == 1
    error = errors[0]
    assert error['reason'] == 'RUNTIME_TYPE_MISMATCH'
    assert not error['stack']['entries']


def field_stack(error_data):
    return [
        entry['field']['name'] for entry in error_data['stack']['entries']
        if entry['__typename'] == 'EvaluationStackPathEntry'
    ]


def test_basic_invalid_config_type_mismatch():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config={
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': 123,
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
    assert error_data['valueRep'] == '123'
    assert error_data['type']['name'] == 'Path'

    assert ['solids', 'load_num_csv', 'config', 'path'] == field_stack(error_data)


def test_basic_invalid_config_missing_field():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config={
            'solids': {
                'load_num_csv': {
                    'config': {},
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

    assert ['solids', 'load_num_csv', 'config'] == field_stack(error_data)
    assert error_data['reason'] == 'MISSING_REQUIRED_FIELD'
    assert error_data['field']['name'] == 'path'


def single_error_data(result):
    assert len(result.data['isPipelineConfigValid']['errors']) == 1
    return result.data['isPipelineConfigValid']['errors'][0]


def test_basic_invalid_not_defined_field():
    result = execute_config_graphql(
        pipeline_name='pandas_hello_world',
        config={
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': 'foo.txt',
                        'extra': 'nope',
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
    assert ['solids', 'load_num_csv', 'config'] == field_stack(error_data)
    assert error_data['reason'] == 'FIELD_NOT_DEFINED'
    assert error_data['fieldName'] == 'extra'


def define_more_complicated_nested_config():
    return PipelineDefinition(
        name='more_complicated_nested_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_config',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=types.Field(
                    types.Dict(
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
                            ),
                            'nested_field':
                            types.Field(
                                types.Dict(
                                    {
                                        'field_four_str':
                                        types.Field(types.String),
                                        'field_five_int':
                                        types.Field(types.Int),
                                        'field_six_nullable_int_list':
                                        types.Field(
                                            types.List(types.Nullable(types.Int)),
                                            is_optional=True,
                                        ),
                                    }
                                )
                            ),
                        },
                    ),
                )
            ),
        ],
    )


TYPE_RENDER_QUERY = '''
fragment innerInfo on Type {
  name
  isDict
  isList
  isNullable
  innerTypes {
    name
  }
  ... on CompositeType {
    fields {
      name
      type {
       name
      }
      isOptional
    }
  }  
}

{
  pipeline(name: "more_complicated_nested_config") { 
    name
    solids {
      name
      definition {
        configDefinition {
          type {
            ...innerInfo
            innerTypes {
              ...innerInfo
            }
          }
        }
      }
    }
  }
}
'''


def test_type_rendering():
    result = execute_dagster_graphql(define_context(), TYPE_RENDER_QUERY)
    assert not result.errors
    assert result.data


def define_context_config_pipeline():
    return PipelineDefinition(
        name='context_config_pipeline',
        solids=[],
        context_definitions={
            'context_one':
            PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None,
                config_field=Field(types.String),
            ),
            'context_two':
            PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None,
                config_field=Field(types.Int),
            ),
            'context_with_resources':
            PipelineContextDefinition(
                resources={
                    'resource_one':
                    ResourceDefinition(
                        resource_fn=lambda *args, **kwargs: None,
                        config_field=Field(types.Int),
                    ),
                    'resource_two':
                    ResourceDefinition(resource_fn=lambda *args, **kwargs: None,
                                       ),
                }
            )
        }
    )


RESOURCE_QUERY = '''
{
  pipeline(name: "context_config_pipeline") {
    contexts {
      name
      resources {
        name
        description
        config {
          type {
            name
            ... on CompositeType {
              fields {
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
}
'''


def test_context_fetch_resources():
    result = execute_dagster_graphql(
        define_context(),
        RESOURCE_QUERY,
    )

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['contexts']


def test_context_config_works():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        config={
            'context': {
                'context_one': {
                    'config': 'kj23k4j3'
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'context_config_pipeline'

    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        config={
            'context': {
                'context_two': {
                    'config': 38934
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationValid'
    assert result.data['isPipelineConfigValid']['pipeline']['name'] == 'context_config_pipeline'


def test_context_config_selector_error():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        config={'context': {}},
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'SELECTOR_FIELD_ERROR'
    assert error_data['incomingFields'] == []


def test_context_config_wrong_selector():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        config={
            'context': {
                'not_defined': {}
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'FIELD_NOT_DEFINED'
    assert error_data['fieldName'] == 'not_defined'


def test_context_config_multiple_selectors():
    result = execute_config_graphql(
        pipeline_name='context_config_pipeline',
        config={
            'context': {
                'context_one': {
                    'config': 'kdjfd'
                },
                'context_two': {
                    'config': 123,
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['isPipelineConfigValid']['__typename'] == 'PipelineConfigValidationInvalid'
    error_data = single_error_data(result)
    assert error_data['reason'] == 'SELECTOR_FIELD_ERROR'
    assert error_data['incomingFields'] == ['context_one', 'context_two']


def test_more_complicated_works():
    result = execute_config_graphql(
        pipeline_name='more_complicated_nested_config',
        config={
            'solids': {
                'a_solid_with_config': {
                    'config': {
                        'field_one': 'foo.txt',
                        'field_two': 'yup',
                        'field_three': 'mmmhmmm',
                        'nested_field': {
                            'field_four_str': 'yaya',
                            'field_five_int': 234,
                        }
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationValid'
    assert valid_data['pipeline']['name'] == 'more_complicated_nested_config'


def test_more_complicated_multiple_errors():
    result = execute_config_graphql(
        pipeline_name='more_complicated_nested_config',
        config={
            'solids': {
                'a_solid_with_config': {
                    'config': {
                        # 'field_one': 'foo.txt', # missing
                        'field_two': 'yup',
                        'field_three': 'mmmhmmm',
                        'extra_one': 'kjsdkfjd',  # extra
                        'nested_field': {
                            'field_four_str': 23434,  # runtime type
                            'field_five_int': 234,
                            'extra_two': 'ksjdkfjd',  # another extra
                        }
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']

    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'more_complicated_nested_config'
    assert len(valid_data['errors']) == 4

    missing_error_one = find_error(
        result,
        ['solids', 'a_solid_with_config', 'config'],
        'MISSING_REQUIRED_FIELD',
    )
    assert ['solids', 'a_solid_with_config', 'config'] == field_stack(missing_error_one)
    assert missing_error_one['reason'] == 'MISSING_REQUIRED_FIELD'
    assert missing_error_one['field']['name'] == 'field_one'

    not_defined_one = find_error(
        result,
        ['solids', 'a_solid_with_config', 'config'],
        'FIELD_NOT_DEFINED',
    )
    assert ['solids', 'a_solid_with_config', 'config'] == field_stack(not_defined_one)
    assert not_defined_one['reason'] == 'FIELD_NOT_DEFINED'
    assert not_defined_one['fieldName'] == 'extra_one'

    runtime_type_error = find_error(
        result,
        ['solids', 'a_solid_with_config', 'config', 'nested_field', 'field_four_str'],
        'RUNTIME_TYPE_MISMATCH',
    )
    assert ['solids', 'a_solid_with_config', 'config', 'nested_field',
            'field_four_str'] == field_stack(runtime_type_error)
    assert runtime_type_error['reason'] == 'RUNTIME_TYPE_MISMATCH'
    assert runtime_type_error['valueRep'] == '23434'
    assert runtime_type_error['type']['name'] == 'String'

    not_defined_two = find_error(
        result,
        ['solids', 'a_solid_with_config', 'config', 'nested_field'],
        'FIELD_NOT_DEFINED',
    )

    assert ['solids', 'a_solid_with_config', 'config',
            'nested_field'] == field_stack(not_defined_two)
    assert not_defined_two['reason'] == 'FIELD_NOT_DEFINED'
    assert not_defined_two['fieldName'] == 'extra_two'

    # TODO: two more errors


def test_config_list():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        config={
            'solids': {
                'solid_with_list': {
                    'config': [1, 2],
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationValid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'


def test_config_list_invalid():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        config={
            'solids': {
                'solid_with_list': {
                    'config': 'foo',
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'
    assert len(valid_data['errors']) == 1
    assert ['solids', 'solid_with_list', 'config'] == field_stack(valid_data['errors'][0])


def test_config_list_item_invalid():
    result = execute_config_graphql(
        pipeline_name='pipeline_with_list',
        config={
            'solids': {
                'solid_with_list': {
                    'config': [1, 'foo'],
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    valid_data = result.data['isPipelineConfigValid']
    assert valid_data['__typename'] == 'PipelineConfigValidationInvalid'
    assert valid_data['pipeline']['name'] == 'pipeline_with_list'
    assert len(valid_data['errors']) == 1
    entries = valid_data['errors'][0]['stack']['entries']
    assert len(entries) == 4
    assert ['solids', 'solid_with_list', 'config'] == field_stack(valid_data['errors'][0])

    last_entry = entries[3]
    assert last_entry['__typename'] == 'EvaluationStackListItemEntry'
    assert last_entry['listIndex'] == 1


def find_error(result, field_stack_to_find, reason):
    llist = list(find_errors(result, field_stack_to_find, reason))
    assert len(llist) == 1
    return llist[0]


def find_errors(result, field_stack_to_find, reason):
    error_datas = result.data['isPipelineConfigValid']['errors']
    for error_data in error_datas:
        if field_stack_to_find == field_stack(error_data) and error_data['reason'] == reason:
            yield error_data


def test_pipelines():
    result = execute_dagster_graphql(define_context(), '{ pipelines { nodes { name } } }')
    assert not result.errors
    assert result.data

    assert set([p['name'] for p in result.data['pipelines']['nodes']]) == set(
        [
            'context_config_pipeline',
            'more_complicated_config',
            'more_complicated_nested_config',
            'pandas_hello_world',
            'pandas_hello_world_two',
            'pipeline_with_list',
        ]
    )


def test_pipelines_or_error():
    result = execute_dagster_graphql(
        define_context(), '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } '
    )
    assert not result.errors
    assert result.data

    assert set([p['name'] for p in result.data['pipelinesOrError']['nodes']]) == set(
        [
            'context_config_pipeline',
            'more_complicated_config',
            'more_complicated_nested_config',
            'pandas_hello_world',
            'pandas_hello_world_two',
            'pipeline_with_list',
        ]
    )


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipeline(name: "pandas_hello_world_two") {
            name
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipeline']['name'] == 'pandas_hello_world_two'


def test_pipeline_or_error_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipelineOrError(name: "pandas_hello_world_two") {
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'pandas_hello_world_two'


EXECUTION_PLAN_QUERY = '''
query PipelineQuery($executionParams: PipelineExecutionParams!) {
  executionPlan(executionParams: $executionParams) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
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
    ... on PipelineNotFoundError {
        pipelineName
    }
  }
}
'''


def test_query_execution_plan_errors():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': 2334893,
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineConfigValidationInvalid'

    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {
            'executionParams': {
                'pipelineName': 'nope',
                'config': 2334893,
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executionPlan']['pipelineName'] == 'nope'


def test_query_execution_plan_snapshot(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': 'pandas_hello_world/num.csv',
                            },
                        },
                    },
                },
            }
        },
    )

    assert not result.errors
    assert result.data

    snapshot.assert_match(result.data)


def test_query_execution_plan():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': 'pandas_hello_world/num.csv',
                            },
                        },
                    },
                },
            }
        },
    )

    if result.errors:
        raise Exception(result.errors[0])

    assert not result.errors
    assert result.data

    plan_data = result.data['executionPlan']

    names = get_nameset(plan_data['steps'])
    assert len(names) == 3

    assert names == set(['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform'])

    assert result.data['executionPlan']['pipeline']['name'] == 'pandas_hello_world'

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
    result = execute_dagster_graphql(define_context(), PRODUCTION_QUERY)

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data


MUTATION_QUERY = '''
mutation ($executionParams: PipelineExecutionParams!) {
    startPipelineExecution(
        executionParams: $executionParams
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { name }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_context(),
        MUTATION_QUERY,
        variables={
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': script_relative_path('num.csv'),
                            }
                        },
                    },
                },
            },
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'pandas_hello_world'


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_context(),
        MUTATION_QUERY,
        variables={
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': 384938439
                            }
                        },
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineConfigValidationInvalid'


def test_basis_start_pipeline_not_found_error():
    result = execute_dagster_graphql(
        define_context(),
        MUTATION_QUERY,
        variables={
            'executionParams': {
                'pipelineName': 'sjkdfkdjkf',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': 'test.csv'
                            }
                        },
                    },
                },
            },
        },
    )

    if result.errors:
        raise Exception(result.errors)

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startPipelineExecution']['pipelineName'] == 'sjkdfkdjkf'


def test_basic_start_pipeline_execution_and_subscribe():
    context = define_context()

    result = execute_dagster_graphql(
        context,
        MUTATION_QUERY,
        variables={
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': script_relative_path('num.csv'),
                            }
                        },
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    run_id = result.data['startPipelineExecution']['run']['runId']
    assert uuid.UUID(run_id)

    subscription = execute_dagster_graphql(
        context,
        parse(SUBSCRIPTION_QUERY),
        variables={'runId': run_id},
    )

    messages = []
    subscription.subscribe(messages.append)

    for m in messages:
        assert not m.errors
        assert m.data
        assert m.data['pipelineRunLogs']


SUBSCRIPTION_QUERY = '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
    }
}
'''


def test_basic_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        SYNC_MUTATION_QUERY,
        variables={
            'executionParams': {
                'pipelineName': 'pandas_hello_world',
                'config': {
                    'solids': {
                        'load_num_csv': {
                            'config': {
                                'path': script_relative_path('num.csv'),
                            }
                        },
                    },
                },
            },
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'INFO'


def first_event_of_type(logs, message_type):
    for log in logs:
        if log['__typename'] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


SYNC_MUTATION_QUERY = '''
mutation ($executionParams: PipelineExecutionParams!) {
    startPipelineExecution(
        executionParams: $executionParams
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { name }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            message
                            level
                        }
                    }
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''
