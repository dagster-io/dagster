from dagster_graphql.test.utils import execute_dagster_graphql
from .setup import define_context

LOGGER_QUERY = '''
{
  pipeline(params: { name: "multi_mode_with_loggers" }) {
    modes {
      name
      loggers {
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


def test_mode_fetch_loggers(snapshot):
    result = execute_dagster_graphql(define_context(), LOGGER_QUERY)

    assert not result.errors
    assert result.data
    assert result.data['pipeline']
    assert result.data['pipeline']['modes']
    for mode_data in result.data['pipeline']['modes']:
        assert mode_data['loggers']

    snapshot.assert_match(result.data)
