from dagster_graphql.test.utils import execute_dagster_graphql
from .setup import define_context

RESOURCE_QUERY = '''
{
  pipeline(params: { name: "multi_mode_with_resources" }) {
    modes {
      name
      resources {
        name
        description
        configField {
          configType {
            name
            ... on CompositeConfigType {
              fields {
                name
                configType {
                  name
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


def test_mode_fetch_resources(snapshot):
    result = execute_dagster_graphql(define_context(), RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['modes']
    for mode_data in result.data['pipeline']['modes']:
        assert mode_data['resources']

    snapshot.assert_match(result.data)
