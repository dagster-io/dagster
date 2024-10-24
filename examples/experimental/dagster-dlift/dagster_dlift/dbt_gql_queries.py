GET_DBT_MODELS_QUERY = """
query GetModelsQuery($environmentId: BigInt!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      models(first: $first) {
        edges {
          node {
            schema
            parents {
              resourceType
              name
              uniqueId
            }
            uniqueId
            tags
            meta
            jobDefinitionId
          }
        }
      }
    }
  }
}
"""

GET_DBT_SOURCES_QUERY = """
query SourcesQuery($environmentId: BigInt!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      sources(first: $first) {
        edges {
          node {
            uniqueId
            sourceName
            resourceType
            sourceDescription
          }
        }
      }
    }
  }
}
"""

GET_DBT_TESTS_QUERY = """
query GetTestsQuery($environmentId: BigInt!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      tests(first: $first) {
        edges {
          node {
            name
            testType
            jobDefinitionId
            parents {
              resourceType
              uniqueId
              name
            }
            rawCode
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
