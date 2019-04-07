from .setup import define_context, execute_dagster_graphql

RESOURCE_QUERY = '''
{
  pipeline(params: { name: "context_config_pipeline" }) {
    contexts {
      name
      resources {
        name
        description
        config {
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


def test_context_fetch_resources():
    result = execute_dagster_graphql(define_context(), RESOURCE_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['contexts']
