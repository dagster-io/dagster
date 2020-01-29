import pytest


@pytest.fixture(scope='session')
def production_query():
    return '''
query AppQuery {
  pipelinesOrError {
    ... on Error {
      message
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
        ... RuntimeTypeWithTooltipFragment
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
    key 
    description
    ... on CompositeConfigType {
      fields {
        name
        description
        isOptional
        defaultValue
        configType {
          key 
          description
          ... on CompositeConfigType {
            fields {
              name
              description
              isOptional
              defaultValue
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
'''
