from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context, define_test_snapshot_context

RUNTIME_TYPE_QUERY = '''
query RuntimeTypeQuery($pipelineName: String! $runtimeTypeName: String!)
{
    pipelineOrError(params:{ name: $pipelineName}) {
        __typename
        ... on Pipeline {
            runtimeTypeOrError(runtimeTypeName: $runtimeTypeName) {
                __typename
                ... on RegularRuntimeType {
                    name
                    displayName
                    isBuiltin
                }
                ... on RuntimeTypeNotFoundError {
                    runtimeTypeName
                }
            }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''

ALL_RUNTIME_TYPES_QUERY = '''
fragment schemaTypeFragment on ConfigType {
  key
  ... on CompositeConfigType {
    fields {
      name
      configType {
        key
      }
    }
    recursiveConfigTypes {
      key
    }
  }
}
fragment runtimeTypeFragment on RuntimeType {
    key
    name
    displayName
    isNullable
    isList
    description
    inputSchemaType {
        ...schemaTypeFragment
    }
    outputSchemaType {
        ...schemaTypeFragment
    }
    innerTypes {
        key
    }
    ... on WrappingRuntimeType {
        ofType {
            key
        }
    }
}

{
 	pipelines {
    nodes {
      name
      runtimeTypes {
        ...runtimeTypeFragment
      }
    }
  }
}
'''


def test_dagster_type_query_works():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'PoorMansDataFrame'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    )
    assert result.data['pipelineOrError']['runtimeTypeOrError']['name'] == 'PoorMansDataFrame'


def test_dagster_type_query_with_container_context_ok():
    result = execute_dagster_graphql(
        define_test_snapshot_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'PoorMansDataFrame'},
    )
    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    )
    assert result.data['pipelineOrError']['runtimeTypeOrError']['name'] == 'PoorMansDataFrame'


def test_dagster_type_builtin_query():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'Int'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    )
    assert result.data['pipelineOrError']['runtimeTypeOrError']['name'] == 'Int'
    assert result.data['pipelineOrError']['runtimeTypeOrError']['isBuiltin']


def test_dagster_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'nope', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['pipelineOrError']['pipelineName'] == 'nope'


def test_dagster_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['runtimeTypeOrError']['__typename']
        == 'RuntimeTypeNotFoundError'
    )
    assert result.data['pipelineOrError']['runtimeTypeOrError']['runtimeTypeName'] == 'nope'


def test_dagster_type_or_error_query_with_container_context_not_found():
    result = execute_dagster_graphql(
        define_test_snapshot_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['runtimeTypeOrError']['__typename']
        == 'RuntimeTypeNotFoundError'
    )
    assert result.data['pipelineOrError']['runtimeTypeOrError']['runtimeTypeName'] == 'nope'


def test_smoke_test_dagster_type_system():
    result = execute_dagster_graphql(define_test_context(), ALL_RUNTIME_TYPES_QUERY)

    assert not result.errors
    assert result.data
