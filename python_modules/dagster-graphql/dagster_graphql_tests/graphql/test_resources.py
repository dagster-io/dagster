from dagster_graphql.test.utils import execute_dagster_graphql

RESOURCE_QUERY = '''
{
  pipelineOrError(params: { name: "multi_mode_with_resources" }) {
    __typename
    ... on Pipeline {
      modes {
        name
        resources {
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

REQUIRED_RESOURCE_QUERY = '''{
  pipelineOrError(params: { name:"required_resource_pipeline" }){
    ... on Pipeline {
      name
      solids {
        definition {
            requiredResources {
              resourceKey
            }
        }
      }
    }
  }
}
'''


def test_mode_fetch_resources(graphql_context, snapshot):
    result = execute_dagster_graphql(graphql_context, RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']
    assert result.data['pipelineOrError']['modes']
    for mode_data in result.data['pipelineOrError']['modes']:
        assert mode_data['resources']

    snapshot.assert_match(result.data)


# Warning: If _compute_fields_hash changes, verify that the result.data has the same shape/keys/values
# as the existing snapshot and then run update snapshot
def test_required_resources(graphql_context, snapshot):
    result = execute_dagster_graphql(graphql_context, REQUIRED_RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['solids']
    [solid] = result.data['pipelineOrError']['solids']
    assert solid
    assert solid['definition']['requiredResources']
    assert solid['definition']['requiredResources'] == [{'resourceKey': 'R1'}]

    snapshot.assert_match(result.data)
