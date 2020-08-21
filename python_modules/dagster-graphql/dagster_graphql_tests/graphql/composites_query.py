COMPOSITES_QUERY = """
query CompositesQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
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
    ... on PythonError {
      message
      stack
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
"""

PARENT_ID_QUERY = """
query withParent($selector: PipelineSelector!, $parentHandleID: String) {
  pipelineOrError(params: $selector) {
    __typename
    ... on Pipeline {
      name
      solidHandles(parentHandleID: $parentHandleID) {
        handleID
      }
    }
  }
}
"""

SOLID_ID_QUERY = """
query solidFetch($selector: PipelineSelector!, $id: String!) {
  pipelineOrError(params: $selector) {
    __typename
    ... on Pipeline {
      name
      solidHandle(handleID: $id) {
        handleID
      }
    }
  }
}
"""

COMPOSITES_QUERY_NESTED_DEPENDS_ON_DEPENDS_BY_CORE = """
query CompositesQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
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
"""


NESTED_INPUT_DEPENDS_ON = """
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
"""

NESTED_OUTPUT_DEPENDED_BY = """
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
"""
