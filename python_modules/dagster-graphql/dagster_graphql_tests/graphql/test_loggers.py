from dagster_graphql.test.utils import execute_dagster_graphql

LOGGER_QUERY = '''
{
  pipelineOrError(params: { name: "multi_mode_with_loggers" }) {
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
'''

# Warning: If _compute_fields_hash changes, verify that the result.data has the same shape/keys/values
# as the existing snapshot and then run update snapshot
def test_mode_fetch_loggers(graphql_context, snapshot):
    result = execute_dagster_graphql(graphql_context, LOGGER_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']
    assert result.data['pipelineOrError']['modes']
    for mode_data in result.data['pipelineOrError']['modes']:
        assert mode_data['loggers']

    snapshot.assert_match(result.data)
