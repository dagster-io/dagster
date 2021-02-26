from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

RUNTIME_TYPE_QUERY = """
query DagsterTypeQuery($selector: PipelineSelector! $dagsterTypeName: String!)
{
    pipelineOrError(params: $selector) {
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
"""

ALL_RUNTIME_TYPES_QUERY = """
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
  repositoriesOrError {
    ... on RepositoryConnection {
      nodes {
        pipelines {
          name
          dagsterTypes {
            ...dagsterTypeFragment
          }
        }
      }
    }
  }
}
"""


def test_dagster_type_query_works(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {
            "selector": selector,
            "dagsterTypeName": "PoorMansDataFrame",
        },
    )

    assert not result.errors
    assert result.data
    assert (
        result.data["pipelineOrError"]["dagsterTypeOrError"]["__typename"] == "RegularDagsterType"
    )
    assert result.data["pipelineOrError"]["dagsterTypeOrError"]["name"] == "PoorMansDataFrame"


def test_dagster_type_builtin_query(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {
            "selector": selector,
            "dagsterTypeName": "Int",
        },
    )

    assert not result.errors
    assert result.data
    assert (
        result.data["pipelineOrError"]["dagsterTypeOrError"]["__typename"] == "RegularDagsterType"
    )
    assert result.data["pipelineOrError"]["dagsterTypeOrError"]["name"] == "Int"
    assert result.data["pipelineOrError"]["dagsterTypeOrError"]["isBuiltin"]


def test_dagster_type_or_error_pipeline_not_found(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "nope")
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {
            "selector": selector,
            "dagsterTypeName": "nope",
        },
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]["__typename"] == "PipelineNotFoundError"
    assert result.data["pipelineOrError"]["pipelineName"] == "nope"


def test_dagster_type_or_error_type_not_found(graphql_context):
    selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
    result = execute_dagster_graphql(
        graphql_context,
        RUNTIME_TYPE_QUERY,
        {
            "selector": selector,
            "dagsterTypeName": "nope",
        },
    )

    assert not result.errors
    assert result.data
    assert (
        result.data["pipelineOrError"]["dagsterTypeOrError"]["__typename"]
        == "DagsterTypeNotFoundError"
    )
    assert result.data["pipelineOrError"]["dagsterTypeOrError"]["dagsterTypeName"] == "nope"


def test_smoke_test_dagster_type_system(graphql_context):
    result = execute_dagster_graphql(graphql_context, ALL_RUNTIME_TYPES_QUERY)

    assert not result.errors
    assert result.data
