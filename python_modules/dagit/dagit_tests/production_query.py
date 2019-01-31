PRODUCTION_QUERY = '''
query AppQuery {
  pipelinesOrError {
    ... on Error {
      message
      stack
      __typename
    }
    ... on PipelineConnection {
      nodes {
        ...PipelineFragment
        __typename
      }
    }
    __typename
  }
}

fragment PipelineFragment on Pipeline {
  name
  description
  solids {
    ...SolidFragment
    __typename
  }
  contexts {
    name
    description
    config {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  ...PipelineGraphFragment
  ...ConfigEditorFragment
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
    configDefinition {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      description
      type {
        ... RuntimeTypeWithTooltipFragment
        __typename
      }
      expectations {
        name
        description
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
      expectations {
        name
        description
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment RuntimeTypeWithTooltipFragment on RuntimeType {
  name
  description
  __typename
}

fragment SolidTypeSignatureFragment on Solid {
  outputs {
    definition {
      name
      type {
        ... RuntimeTypeWithTooltipFragment
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
        ... RuntimeTypeWithTooltipFragment
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
    name
    description
    ... on CompositeConfigType {
      fields {
        name
        description
        isOptional
        defaultValue
        configType {
          name
          description
          ... on CompositeConfigType {
            fields {
              name
              description
              isOptional
              defaultValue
              configType {
                name
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
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigEditorFragment on Pipeline {
  name
  ...ConfigExplorerFragment
  __typename
}

fragment ConfigExplorerFragment on Pipeline {
  contexts {
    name
    description
    config {
      ...ConfigFieldFragment
      __typename
    }
    __typename
  }
  solids {
    definition {
      name
      description
      configDefinition {
        ...ConfigFieldFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}
'''
