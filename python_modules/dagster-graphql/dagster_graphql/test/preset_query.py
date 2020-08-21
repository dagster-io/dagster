from .utils import execute_dagster_graphql, infer_pipeline_selector

PRESETS_QUERY = """
query PresetsQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    ... on Pipeline {
      name
      presets {
        __typename
        name
        solidSelection
        runConfigYaml
        mode
      }
    }
  }
}
"""


def execute_preset_query(pipeline_name, context):
    selector = infer_pipeline_selector(context, pipeline_name)
    return execute_dagster_graphql(context, PRESETS_QUERY, variables={"selector": selector})
