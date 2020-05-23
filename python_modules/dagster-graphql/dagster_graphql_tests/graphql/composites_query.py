COMPOSITES_QUERY = '''
query CompositesQuery {
  pipelineOrError(params: { name: "composites_pipeline" }) {
    __typename
    ... on Pipeline {
      name
      solidHandles {
        handleID
        solid {
          ...SolidInfo
        }
      }
    }
  }
}

fragment SolidInfo on Solid {
  name
  inputs {
    definition {
      name
    }
    dependsOn {
      solid {
        name
      }
    }
  }
  outputs {
    definition {
      name
    }
    dependedBy {
      solid {
        name
      }
    }
  }
  definition {
    ... on CompositeSolidDefinition {
      solids { name }
      inputMappings {
        definition { name }
        mappedInput {
          definition { name }
          solid { name }
        }
      }
      outputMappings {
        definition {
          name
        }
        mappedOutput {
          definition { name }
          solid { name }
        }
      }
    }
  }
}
'''

PARENT_ID_QUERY = '''
query withParent($parentHandleID: String) {
  pipelineOrError(params: { name: "composites_pipeline" }) {
    __typename
    ... on Pipeline {
      name
      solidHandles(parentHandleID: $parentHandleID) {
        handleID
      }
    }
  }
}
'''

SOLID_ID_QUERY = '''
query solidFetch($id: String!) {
  pipelineOrError(params: { name: "composites_pipeline" }) {
    __typename
    ... on Pipeline {
      name
      solidHandle(handleID: $id) {
        handleID
      }
    }
  }
}
'''

COMPOSITES_QUERY_NESTED_DEPENDS_ON_DEPENDS_BY_CORE = '''
query CompositesQuery {
  pipelineOrError(params: { name: "composites_pipeline" }) {
    __typename
    ... on Pipeline {
      name
      solidHandles {
        handleID
        solid {
          ...SolidInfo
        }
      }
    }
  }
}
'''


NESTED_INPUT_DEPENDS_ON = '''
fragment SolidInfo on Solid {
  outputs {
    dependedBy {
      solid {
        name
        inputs {
          definition { name }
          dependsOn {
            definition {
              name
            }
          }
        }
      }
    }
  }
}
'''

NESTED_OUTPUT_DEPENDED_BY = '''
fragment SolidInfo on Solid {
  name
  inputs {
    definition {
      name
    }
    dependsOn {
      solid {
        name
        outputs {
          dependedBy {
            definition { name }
          }
        }
      }
    }
  }
}
'''
