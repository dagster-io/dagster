from dagster_graphql.test.utils import execute_dagster_graphql

RUNTIME_TYPE_QUERY = '''
query DagsterTypeQuery($pipelineName: String! $dagsterTypeName: String!)
{
    pipelineOrError(params:{ name: $pipelineName}) {
        __typename
        ... on Pipeline {
            dagsterTypeOrError(dagsterTypeName: $dagsterTypeName) {
                __typename
                ... on RegularDagsterType {
                    name
                    displayName
                    isBuiltin
                }
                ... on DagsterTypeNotFoundError {
                    dagsterTypeName
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
fragment dagsterTypeFragment on DagsterType {
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
    ... on WrappingDagsterType {
        ofType {
            key
        }
    }
}

{
 	pipelines {
    nodes {
      name
      dagsterTypes {
        ...dagsterTypeFragment
      }
    }
  }
}
'''


def test_dagster_type_query_works(graphql_context):
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'dagsterTypeName': 'PoorMansDataFrame'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['dagsterTypeOrError']['__typename'] == 'RegularDagsterType'
    )
    assert result.data['pipelineOrError']['dagsterTypeOrError']['name'] == 'PoorMansDataFrame'


def test_dagster_type_builtin_query(graphql_context):
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'dagsterTypeName': 'Int'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['dagsterTypeOrError']['__typename'] == 'RegularDagsterType'
    )
    assert result.data['pipelineOrError']['dagsterTypeOrError']['name'] == 'Int'
    assert result.data['pipelineOrError']['dagsterTypeOrError']['isBuiltin']


def test_dagster_type_or_error_pipeline_not_found(graphql_context):
    result = execute_dagster_graphql(
        graphql_context, RUNTIME_TYPE_QUERY, {'pipelineName': 'nope', 'dagsterTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['pipelineOrError']['pipelineName'] == 'nope'


def test_dagster_type_or_error_type_not_found(graphql_context):
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {'pipelineName': 'csv_hello_world', 'dagsterTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['pipelineOrError']['dagsterTypeOrError']['__typename']
        == 'DagsterTypeNotFoundError'
    )
    assert result.data['pipelineOrError']['dagsterTypeOrError']['dagsterTypeName'] == 'nope'


def test_smoke_test_dagster_type_system(graphql_context):
    result = execute_dagster_graphql(graphql_context, ALL_RUNTIME_TYPES_QUERY)

    assert not result.errors
    assert result.data
