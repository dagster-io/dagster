from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context

RESOURCE_QUERY = '''
{
  pipeline(params: { name: "multi_mode_with_resources" }) {
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
  pipeline(params: { name:"required_resource_pipeline" }){
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
'''


def test_mode_fetch_resources(snapshot):
    result = execute_dagster_graphql(define_test_context(), RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['modes']
    for mode_data in result.data['pipeline']['modes']:
        assert mode_data['resources']

    snapshot.assert_match(result.data)


# Warning: If _compute_fields_hash changes, verify that the result.data has the same shape/keys/values
# as the existing snapshot and then run update snapshot
def test_required_resources(snapshot):
    result = execute_dagster_graphql(define_test_context(), REQUIRED_RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']['solids']
    [solid] = result.data['pipeline']['solids']
    assert solid
    assert solid['definition']['requiredResources']
    assert solid['definition']['requiredResources'] == [{'resourceKey': 'R1'}]

    snapshot.assert_match(result.data)
