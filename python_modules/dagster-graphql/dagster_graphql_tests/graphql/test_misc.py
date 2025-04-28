import csv
from collections import OrderedDict

from dagster import (
    DependencyDefinition,
    In,
    JobDefinition,
    OpDefinition,
    dagster_type_loader,
    repository,
)
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.types.dagster_type import PythonObjectDagsterType
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._legacy import OutputDefinition
from dagster_graphql.schema.roots.mutation import execution_params_from_graphql
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.production_query import PRODUCTION_QUERY


@dagster_type_loader(str)
def df_input_schema(_context, path):
    with open(path, encoding="utf8") as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name="PoorMansDataFrame",
    loader=df_input_schema,
)


def test_enum_query(graphql_context: WorkspaceRequestContext):
    selector = infer_job_selector(graphql_context, "job_with_enum_config")

    ENUM_QUERY = """
    query EnumQuery($selector: PipelineSelector!) {
      runConfigSchemaOrError(selector: $selector) {
        ... on RunConfigSchema {
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
    """

    result = execute_dagster_graphql(
        graphql_context,
        ENUM_QUERY,
        {
            "selector": selector,
        },
    )

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data["runConfigSchemaOrError"]["allConfigTypes"]:
        if td["key"] == "TestEnum":
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data["key"] == "TestEnum"
    assert enum_type_data["values"] == [
        {"value": "ENUM_VALUE_ONE", "description": "An enum value."},
        {"value": "ENUM_VALUE_TWO", "description": "An enum value."},
        {"value": "ENUM_VALUE_THREE", "description": "An enum value."},
    ]


TYPE_RENDER_QUERY = """
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
      isRequired
    }
  }
}

query TypeRenderQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
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
"""


def test_type_rendering(graphql_context: WorkspaceRequestContext):
    selector = infer_job_selector(graphql_context, "more_complicated_nested_config")
    result = execute_dagster_graphql(graphql_context, TYPE_RENDER_QUERY, {"selector": selector})
    assert not result.errors
    assert result.data


def define_circular_dependency_job():
    return JobDefinition(
        graph_def=GraphDefinition(
            name="circular_dependency_job",
            node_defs=[
                OpDefinition(
                    name="csolid",
                    ins={"num": In("num", PoorMansDataFrame)},  # pyright: ignore[reportArgumentType]
                    outs={"result": OutputDefinition(PoorMansDataFrame)},  # pyright: ignore[reportArgumentType]
                    compute_fn=lambda *_args: None,
                )
            ],
            dependencies={"csolid": {"num": DependencyDefinition("csolid")}},
        )
    )


@repository  # pyright: ignore[reportArgumentType]
def test_repository():
    return {"jobs": {"circular_dependency_job": define_circular_dependency_job}}


def test_pipeline_or_error_by_name(graphql_context: WorkspaceRequestContext):
    selector = infer_job_selector(graphql_context, "csv_hello_world_two")
    result = execute_dagster_graphql(
        graphql_context,
        """
    query NamedPipelineQuery($selector: PipelineSelector!) {
        pipelineOrError(params: $selector) {
            ... on Pipeline {
                name
            }
        }
    }""",
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]["name"] == "csv_hello_world_two"


def test_pipeline_or_error_by_name_not_found(graphql_context: WorkspaceRequestContext):
    selector = infer_job_selector(graphql_context, "foobar")
    result = execute_dagster_graphql(
        graphql_context,
        """
        query NamedPipelineQuery($selector: PipelineSelector!) {
            pipelineOrError(params: $selector) {
                __typename
                ... on Pipeline {
                    name
                }
            }
        }""",
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]["__typename"] == "PipelineNotFoundError"


def test_production_query(graphql_context: WorkspaceRequestContext):
    result = execute_dagster_graphql(graphql_context, PRODUCTION_QUERY)

    assert not result.errors
    assert result.data


def test_params_from_graphql():
    selector = {
        "repositoryName": "repo",
        "repositoryLocationName": "rl",
        "jobName": "job",
    }
    assert execution_params_from_graphql(
        {
            "selector": selector,
        }
    )
    assert execution_params_from_graphql(
        {
            "selector": selector,
            "runConfigData": "{}",
        }
    )
    assert execution_params_from_graphql(
        {
            "selector": selector,
            "runConfigData": "\n\n",
        }
    )
    assert execution_params_from_graphql(
        {
            "selector": selector,
            "runConfigData": "",
        }
    )


def test_repo_not_found(graphql_context: WorkspaceRequestContext):
    selector = {
        "repositoryLocationName": "junk",
        "repositoryName": "junk",
    }
    result = execute_dagster_graphql(
        graphql_context,
        """
        query repo($selector: RepositorySelector!) {
          repositoryOrError(repositorySelector: $selector) {
            __typename
          }
        }""",
        {"selector": selector},
    )
    assert not result.errors
    assert result.data["repositoryOrError"]["__typename"] == "RepositoryNotFoundError"

    result = execute_dagster_graphql(
        graphql_context,
        """
        query repos($selector: RepositorySelector!) {
          repositoriesOrError(repositorySelector: $selector) {
            __typename
          }
        }""",
        {"selector": selector},
    )
    assert not result.errors
    assert result.data["repositoriesOrError"]["__typename"] == "RepositoryNotFoundError"
