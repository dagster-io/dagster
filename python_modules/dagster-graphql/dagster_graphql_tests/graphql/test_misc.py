import os
import sys


from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    check,
)

from dagster.cli.dynamic_loader import RepositoryContainer
from dagster.core.types.config import ALL_CONFIG_BUILTINS

from dagster.utils import script_relative_path

from dagster_pandas import DataFrame

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage

from .setup import define_context, define_repository, execute_dagster_graphql

# This is needed to find production query in all cases
sys.path.insert(0, os.path.abspath(script_relative_path('.')))

from production_query import (  # pylint: disable=wrong-import-position,wrong-import-order
    PRODUCTION_QUERY,
)


def test_enum_query():
    ENUM_QUERY = '''{
  pipeline(params: { name:"pipeline_with_enum_config" }){
    name
    configTypes {
      __typename
      name
      ... on EnumConfigType {
        values
        {
          value
          description
        }
      }
    }
  }
}
'''

    result = execute_dagster_graphql(define_context(), ENUM_QUERY)

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data['pipeline']['configTypes']:
        if td['name'] == 'TestEnum':
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data['name'] == 'TestEnum'
    assert enum_type_data['values'] == [
        {'value': 'ENUM_VALUE_ONE', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_TWO', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_THREE', 'description': 'An enum value.'},
    ]


TYPE_RENDER_QUERY = '''
fragment innerInfo on ConfigType {
  name
  isList
  isNullable
  innerTypes {
    name
  }
  ... on CompositeConfigType {
    fields {
      name
      configType {
       name
      }
      isOptional
    }
  }  
}

{
  pipeline(params: { name: "more_complicated_nested_config" }) { 
    name
    solids {
      name
      definition {
        configDefinition {
          configType {
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


def define_circular_dependency_pipeline():
    return PipelineDefinition(
        name='circular_dependency_pipeline',
        solids=[
            SolidDefinition(
                name='csolid',
                inputs=[InputDefinition('num', DataFrame)],
                outputs=[OutputDefinition(DataFrame)],
                transform_fn=lambda *_args: None,
            )
        ],
        dependencies={'csolid': {'num': DependencyDefinition('csolid')}},
    )


def test_pipelines():
    result = execute_dagster_graphql(define_context(), '{ pipelines { nodes { name } } }')
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelines']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error():
    result = execute_dagster_graphql(
        define_context(), '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } '
    )
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelinesOrError']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error_invalid():
    repository = RepositoryDefinition(
        name='test', pipeline_dict={'pipeline': define_circular_dependency_pipeline}
    )
    context = DagsterGraphQLContext(
        RepositoryContainer(repository=repository),
        PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )
    result = execute_dagster_graphql(
        context, '{ pipelinesOrError { ... on InvalidDefinitionError { message } } }'
    )
    msg = result.data['pipelinesOrError']['message']
    assert "Circular reference detected in solid csolid" in msg


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipeline(params: {name: "pandas_hello_world_two"}) {
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
        pipelineOrError(params: { name: "pandas_hello_world_two" }) {
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'pandas_hello_world_two'


def pipeline_named(result, name):
    for pipeline_data in result.data['pipelines']['nodes']:
        if pipeline_data['name'] == name:
            return pipeline_data
    check.failed('Did not find')


def has_config_type_with_key_prefix(pipeline_data, prefix):
    for config_type_data in pipeline_data['configTypes']:
        if config_type_data['key'].startswith(prefix):
            return True

    return False


def has_config_type(pipeline_data, name):
    for config_type_data in pipeline_data['configTypes']:
        if config_type_data['name'] == name:
            return True

    return False


def test_smoke_test_config_type_system():
    result = execute_dagster_graphql(define_context(), ALL_CONFIG_TYPES_QUERY)

    assert not result.errors
    assert result.data

    pipeline_data = pipeline_named(result, 'more_complicated_nested_config')

    assert pipeline_data

    assert has_config_type_with_key_prefix(pipeline_data, 'Dict.')
    assert not has_config_type_with_key_prefix(pipeline_data, 'List.')
    assert not has_config_type_with_key_prefix(pipeline_data, 'Nullable.')

    for builtin_config_type in ALL_CONFIG_BUILTINS:
        assert has_config_type(pipeline_data, builtin_config_type.name)


ALL_CONFIG_TYPES_QUERY = '''
fragment configTypeFragment on ConfigType {
  __typename
  key
  name
  description
  isNullable
  isList
  isSelector
  isBuiltin
  isSystemGenerated
  innerTypes {
    key
    name
    description
    ... on CompositeConfigType {
        fields {
            name
            isOptional
            description
        }
    }
    ... on WrappingConfigType {
        ofType { key }
    }
  }
  ... on EnumConfigType {
    values {
      value
      description
    }
  }
  ... on CompositeConfigType {
    fields {
      name
      isOptional
      description
    }
  }
  ... on WrappingConfigType {
    ofType { key }
  }
}

{
 	pipelines {
    nodes {
      name
      configTypes {
        ...configTypeFragment
      }
    }
  } 
}
'''

CONFIG_TYPE_QUERY = '''
query ConfigTypeQuery($pipelineName: String! $configTypeName: String!)
{
    configTypeOrError(
        pipelineName: $pipelineName
        configTypeName: $configTypeName
    ) {
        __typename
        ... on RegularConfigType {
            name
        }
        ... on CompositeConfigType {
            name
            innerTypes { key name }
            fields { name configType { key name } }
        }
        ... on EnumConfigType {
            name
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on ConfigTypeNotFoundError {
            pipeline { name }
            configTypeName
        }
    }
}
'''


def test_config_type_or_error_query_success():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert result.data['configTypeOrError']['name'] == 'PandasHelloWorld.Environment'


def test_config_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'nope', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['configTypeOrError']['pipelineName'] == 'nope'


def test_config_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'ConfigTypeNotFoundError'
    assert result.data['configTypeOrError']['pipeline']['name'] == 'pandas_hello_world'
    assert result.data['configTypeOrError']['configTypeName'] == 'nope'


def test_config_type_or_error_nested_complicated():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {
            'pipelineName': 'more_complicated_nested_config',
            'configTypeName': (
                'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
            ),
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert (
        result.data['configTypeOrError']['name']
        == 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
    )
    assert len(result.data['configTypeOrError']['innerTypes']) == 6


def test_production_query():
    result = execute_dagster_graphql(define_context(), PRODUCTION_QUERY)

    assert not result.errors
    assert result.data


ALL_TYPES_QUERY = '''
{
  pipelinesOrError {
    __typename
    ... on PipelineConnection {
      nodes {
        runtimeTypes {
          __typename
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
        __typename
      }
    }
  }
}
'''


def test_production_config_editor_query():
    result = execute_dagster_graphql(define_context(), ALL_TYPES_QUERY)

    assert not result.errors
    assert result.data
