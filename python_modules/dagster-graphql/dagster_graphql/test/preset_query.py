from .utils import execute_dagster_graphql

PRESETS_QUERY = '''
query PresetsQuery($name: String!) {
  pipeline(params: { name: $name }) {
    name
    presets {
      __typename
      name
      solidSubset
      environmentConfigYaml
      mode
    }
  }
}  
'''


def execute_preset_query(pipeline_name, context):
    return execute_dagster_graphql(context, PRESETS_QUERY, variables={'name': pipeline_name})
