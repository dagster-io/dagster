from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

LOGGER_QUERY = """
query LoggerQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    __typename
    ... on Pipeline {
      modes {
        name
        loggers {
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
      }
    }
  }
}
"""

# Warning: If _compute_fields_hash changes, verify that the result.data has the same shape/keys/values
# as the existing snapshot and then run update snapshot
def test_mode_fetch_loggers(graphql_context, snapshot):
    selector = infer_pipeline_selector(graphql_context, "multi_mode_with_loggers")
    result = execute_dagster_graphql(graphql_context, LOGGER_QUERY, {"selector": selector})

    assert not result.errors
    assert result.data
    assert result.data["pipelineOrError"]
    assert result.data["pipelineOrError"]["modes"]
    for mode_data in result.data["pipelineOrError"]["modes"]:
        assert mode_data["loggers"]

    snapshot.assert_match(result.data)
