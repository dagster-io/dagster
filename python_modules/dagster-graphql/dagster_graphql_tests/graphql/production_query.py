PRODUCTION_QUERY = """
query AppQuery {
  repositoriesOrError {
    ... on PythonError {
      message
      stack
    }
    ... on RepositoryConnection {
      nodes {
        pipelines {
          ...PipelineFragment
        }
      }
    }
  }
}


fragment PipelineFragment on Pipeline {
  name
  description
  tags {
    key
    value
  }
  solids {
    ...SolidFragment
    __typename
  }
  modes {
    name
    description
    resources {
      name
      configField {
        ...ConfigFieldFragment
        __typename
      }
    }
  }
  ...PipelineGraphFragment
  __typename
}

fragment SolidFragment on Solid {
  ...SolidTypeSignatureFragment
  name
  definition {
    description
    metadata {
      key
      value
      __typename
    }
    ... on SolidDefinition {
      inputDefinitions {
        name
        description
        type { key }
      }
      outputDefinitions {
        name
        description
        type { key }
      }
      configField {
        ...ConfigFieldFragment
        __typename
      }
    }
    __typename
  }
  inputs {
    definition {
      name
      description
      type {
        ... DagsterTypeWithTooltipFragment
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      description
      type {
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment DagsterTypeWithTooltipFragment on DagsterType {
  name
  description
  __typename
}

fragment SolidTypeSignatureFragment on Solid {
  outputs {
    definition {
      name
      type {
        ... DagsterTypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      type {
        ... DagsterTypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigFieldFragment on ConfigTypeField {
  configType {
    __typename
    key
    description
    ... on CompositeConfigType {
      fields {
        name
        description
        isRequired
        configType {
          key
          description
          ... on CompositeConfigType {
            fields {
              name
              description
              isRequired
              configType {
                key
                description
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
  }
  __typename
}

fragment PipelineGraphFragment on Pipeline {
  name
  solids {
    ...SolidNodeFragment
    __typename
  }
  __typename
}

fragment SolidNodeFragment on Solid {
  name
  inputs {
    definition {
      name
      type {
        name
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      type {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}
"""
