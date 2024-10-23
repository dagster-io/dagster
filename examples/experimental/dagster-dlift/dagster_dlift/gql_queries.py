GET_DBT_MODELS_QUERY = """
query GetModelsQuery($environmentId: BigInt!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      models(first: $first) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            schema
            parents {
              uniqueId
            }
            uniqueId
            tags
          }
        }
      }
    }
  }
}
"""

GET_DBT_SOURCES_QUERY = """
query GetSourcesQuery($environmentId: BigInt!, $first: Int) {
  environment(id: $environmentId) {
    definition {
      sources(first: $first) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            schema
            uniqueId
            tags
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
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            parents {
              uniqueId
              resourceType
            }
            uniqueId
            name
            tags
          }
        }
      }
    }
  }
}
"""

VERIFICATION_QUERY = """
query VerificationQuery($environmentId: BigInt!) {
  environment(id: $environmentId) {
    __typename
  }
}
"""
