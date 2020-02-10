from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context

RUNTIME_TYPE_QUERY = '''
query RuntimeTypeQuery($pipelineName: String! $runtimeTypeName: String!)
{
    runtimeTypeOrError(
        pipelineName: $pipelineName
        runtimeTypeName: $runtimeTypeName
    ) {
        __typename
        ... on RegularRuntimeType {
            name
            displayName
            isBuiltin
        }
        ... on PipelineNotFoundError {
            pipelineName 
        }
        ... on RuntimeTypeNotFoundError {
            pipeline { name }
            runtimeTypeName
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


def test_runtime_type_query_works():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'PoorMansDataFrame'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    assert result.data['runtimeTypeOrError']['name'] == 'PoorMansDataFrame'


def test_runtime_type_builtin_query():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'Int'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'RegularRuntimeType'
    assert result.data['runtimeTypeOrError']['name'] == 'Int'
    assert result.data['runtimeTypeOrError']['isBuiltin']


def test_runtime_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'nope', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['runtimeTypeOrError']['pipelineName'] == 'nope'


def test_runtime_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_test_context(),
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'runtimeTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['runtimeTypeOrError']['__typename'] == 'RuntimeTypeNotFoundError'
    assert result.data['runtimeTypeOrError']['pipeline']['name'] == 'csv_hello_world'
    assert result.data['runtimeTypeOrError']['runtimeTypeName'] == 'nope'


def test_smoke_test_runtime_type_system():
    result = execute_dagster_graphql(define_test_context(), ALL_RUNTIME_TYPES_QUERY)

    assert not result.errors
    assert result.data
