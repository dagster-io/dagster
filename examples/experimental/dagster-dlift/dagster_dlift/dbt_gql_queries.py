GET_DBT_MODELS_QUERY = """
query GetModelsQuery($environmentId: BigInt!, $types: [AncestorNodeType!]!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      models(first: $first) {
        edges {
          node {
            schema
            ancestors(types: $types) {
              description
              name
              uniqueId
            }
            uniqueId
            tags
            meta
          }
        }
      }
    }
  }
}
"""

GET_DBT_RUNS_QUERY = """
query GetRunsQuery($environmentId: BigInt!, $uniqueId: String!) {
  environment(id: $environmentId) {
    applied {
      modelHistoricalRuns(uniqueId: $uniqueId) {
        jobId
        runId
        name
        runResults {
          status
        }
      }
    }
  }
}
"""
