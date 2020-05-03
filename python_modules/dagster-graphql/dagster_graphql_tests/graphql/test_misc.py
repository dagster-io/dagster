import csv
from collections import OrderedDict

import pytest
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.schema.errors import DauphinPipelineNotFoundError
from dagster_graphql.test.utils import execute_dagster_graphql
from dagster_graphql_tests.graphql.setup import (
    define_repository,
    define_test_context,
    define_test_snapshot_context,
)

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Materialization,
    OutputDefinition,
    PipelineDefinition,
    PythonObjectDagsterType,
    RepositoryDefinition,
    SolidDefinition,
    input_hydration_config,
    output_materialization_config,
)


@input_hydration_config(str)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@output_materialization_config(str)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name='PoorMansDataFrame',
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def test_enum_query():
    ENUM_QUERY = '''{
    environmentSchemaOrError(selector: {name: "pipeline_with_enum_config" } ) {
      ... on EnvironmentSchema {
        allConfigTypes {
          __typename
          key
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
  }
  '''

    result = execute_dagster_graphql(define_test_context(), ENUM_QUERY)

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data['environmentSchemaOrError']['allConfigTypes']:
        if td['key'] == 'TestEnum':
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data['key'] == 'TestEnum'
    assert enum_type_data['values'] == [
        {'value': 'ENUM_VALUE_ONE', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_TWO', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_THREE', 'description': 'An enum value.'},
    ]


TYPE_RENDER_QUERY = '''
fragment innerInfo on ConfigType {
  key
  recursiveConfigTypes {
    key
  }
  ... on CompositeConfigType {
    fields {
      name
      configType {
        key
      }
      isOptional
    }
  }
}

{
  pipeline(params: { name: "more_complicated_nested_config" }) {
    __typename
    ... on Pipeline {
      name
      solids {
        name
        definition {
          ... on SolidDefinition {
            configField {
              configType {
                ...innerInfo
                recursiveConfigTypes {
                  ...innerInfo
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


def test_type_rendering():
    result = execute_dagster_graphql(define_test_context(), TYPE_RENDER_QUERY)
    assert not result.errors
    assert result.data


def define_circular_dependency_pipeline():
    return PipelineDefinition(
        name='circular_dependency_pipeline',
        solid_defs=[
            SolidDefinition(
                name='csolid',
                input_defs=[InputDefinition('num', PoorMansDataFrame)],
                output_defs=[OutputDefinition(PoorMansDataFrame)],
                compute_fn=lambda *_args: None,
            )
        ],
        dependencies={'csolid': {'num': DependencyDefinition('csolid')}},
    )


def test_pipelines():
    result = execute_dagster_graphql(define_test_context(), '{ pipelines { nodes { name } } }')
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelines']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error():
    result = execute_dagster_graphql(
        define_test_context(),
        '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } ',
    )
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelinesOrError']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error_with_container_context():
    result = execute_dagster_graphql(
        define_test_snapshot_context(),
        '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } ',
    )
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelinesOrError']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def define_test_repository():
    return RepositoryDefinition(
        name='test', pipeline_dict={'pipeline': define_circular_dependency_pipeline}
    )


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_test_context(),
        '''
    {
        pipeline(params: {name: "csv_hello_world_two"}) {
            name
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipeline']['name'] == 'csv_hello_world_two'


def test_pipeline_by_name_not_found():
    with pytest.raises(UserFacingGraphQLError) as exc:
        execute_dagster_graphql(
            define_test_context(),
            '''
        {
            pipeline(params: {name: "gkjhds"}) {
              name
            }
        }''',
        )

    assert isinstance(exc.value.dauphin_error, DauphinPipelineNotFoundError)


def test_pipeline_or_error_by_name():
    result = execute_dagster_graphql(
        define_test_context(),
        '''
    {
        pipelineOrError(params: { name: "csv_hello_world_two" }) {
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'csv_hello_world_two'


def test_pipeline_or_error_by_name_not_found():
    result = execute_dagster_graphql(
        define_test_context(),
        '''
    {
        pipelineOrError(params: { name: "foobar" }) {
          __typename
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'PipelineNotFoundError'


def test_pipeline_or_error_with_container_context():
    result = execute_dagster_graphql(
        define_test_snapshot_context(),
        '''
        { 
            pipelineOrError(params: {name: "csv_hello_world_two" }) { 
                __typename
                ... on Pipeline {
                    name
                }
            } 
        }
        ''',
    )
    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'csv_hello_world_two'


def test_pipeline_or_error_with_container_context_preset_empty_ok():
    result = execute_dagster_graphql(
        define_test_snapshot_context(),
        '''
        { 
            pipelineOrError(params: {name: "csv_hello_world" }) { 
                __typename
                ... on Pipeline {
                    name
                    presets {
                        name
                    }
                }
            } 
        }
        ''',
    )
    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'csv_hello_world'


def test_production_query(production_query):
    result = execute_dagster_graphql(define_test_context(), production_query)

    assert not result.errors
    assert result.data
