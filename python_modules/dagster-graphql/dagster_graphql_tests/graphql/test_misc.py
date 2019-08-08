import csv
from collections import OrderedDict

from dagster import (
    DependencyDefinition,
    ExecutionTargetHandle,
    InputDefinition,
    Materialization,
    OutputDefinition,
    Path,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    as_dagster_type,
    input_hydration_config,
    output_materialization_config,
)

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import InMemoryRunStorage
from dagster_graphql.test.utils import execute_dagster_graphql
from dagster_graphql_tests.graphql.setup import define_context, define_repository


class PoorMansDataFrame_(list):
    pass


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return PoorMansDataFrame_(
            [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]
        )


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = as_dagster_type(
    PoorMansDataFrame_,
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
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
        ... on SolidDefinition {
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
}
'''


def test_type_rendering():
    result = execute_dagster_graphql(define_context(), TYPE_RENDER_QUERY)
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


def define_test_repository():
    return RepositoryDefinition(
        name='test', pipeline_dict={'pipeline': define_circular_dependency_pipeline}
    )


def test_pipelines_or_error_invalid():

    context = DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(define_test_repository),
        pipeline_runs=InMemoryRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )

    result = execute_dagster_graphql(
        context, '{ pipelinesOrError { ... on InvalidDefinitionError { message } } }'
    )
    msg = result.data['pipelinesOrError']['message']
    assert 'circular reference detected in solid "csolid"' in msg


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_context(),
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


def test_pipeline_or_error_by_name():
    result = execute_dagster_graphql(
        define_context(),
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


def test_production_query(production_query):
    result = execute_dagster_graphql(define_context(), production_query)

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
