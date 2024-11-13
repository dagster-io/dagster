from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

RESOURCE_QUERY = """
query ResourceQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    __typename
    ... on Pipeline {
      modes {
        name
        resources {
          ...ResourceInfo
        }
      }
    }
  }
  resourcesOrError(pipelineSelector: $selector) {
    __typename
    ... on ResourceConnection {
      resources {
        ...ResourceInfo
      }
    }
  }
}

fragment ResourceInfo on Resource {
  name
  description
  configField {
    configType {
      key
      ... on CompositeConfigType {
        fields {
          name
          configType {
            key
          }
        }
      }
    }
  }
}
"""

REQUIRED_RESOURCE_QUERY = """
query RequiredResourceQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    ... on Pipeline {
      name
      solids {
        definition {
          ... on SolidDefinition {
            requiredResources {
              resourceKey
            }
          }
        }
      }
    }
  }
}
"""


def test_mode_fetch_resources(graphql_context: WorkspaceRequestContext, snapshot):
    selector = infer_job_selector(graphql_context, "required_resource_job")
    result = execute_dagster_graphql(
        graphql_context,
        RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]
    assert len(result.data["pipelineOrError"]["modes"]) == 1
    assert result.data["pipelineOrError"]["modes"][0]["resources"]
    assert (
        result.data["pipelineOrError"]["modes"][0]["resources"]
        == result.data["resourcesOrError"]["resources"]
    )

    snapshot.assert_match(result.data)


# Warning: If _compute_fields_hash changes, verify that the result.data has the same shape/keys/values
# as the existing snapshot and then run update snapshot
def test_required_resources(graphql_context: WorkspaceRequestContext, snapshot):
    selector = infer_job_selector(graphql_context, "required_resource_job")
    result = execute_dagster_graphql(
        graphql_context,
        REQUIRED_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]["solids"]
    [solid] = result.data["pipelineOrError"]["solids"]
    assert solid
    assert solid["definition"]["requiredResources"]
    assert solid["definition"]["requiredResources"] == [{"resourceKey": "R1"}]

    snapshot.assert_match(result.data)
