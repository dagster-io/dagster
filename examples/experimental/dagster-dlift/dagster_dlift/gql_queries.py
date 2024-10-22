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

VERIFICATION_QUERY = """
query VerificationQuery($environmentId: BigInt!) {
  environment(id: $environmentId) {
    __typename
  }
}
"""
