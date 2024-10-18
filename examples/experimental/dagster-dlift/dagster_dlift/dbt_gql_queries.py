GET_DBT_MODELS_QUERY = """
query ExampleQuery($environmentId: BigInt!, $types: [AncestorNodeType!]!, $first: Int) {
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
