from dagster_graphql.test.utils import execute_dagster_graphql
from .setup import define_context

COMPOSITES_QUERY = '''
query CompositesQuery {
  pipeline(params: { name: "composites_pipeline" }) {
    name
    solidHandles {
      handleID
      solid {
        ...SolidInfo
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
      inputMappings {
		definition {name}
        mappedInput {
          definition {name}
          solid {name}
        }
      }
	  outputMappings {
        definition {name}
        mappedOutput {
          definition {name}
          solid {name}
        }
      }
    }
  }
}
'''


def test_composites(snapshot):
    result = execute_dagster_graphql(define_context(), COMPOSITES_QUERY)
    handle_map = {}

    for obj in result.data["pipeline"]["solidHandles"]:
        handle_map[obj["handleID"]] = obj["solid"]

    # 10 total solids in the composite pipeline:
    #
    # (+1) \
    #       (+2)
    # (+1) /    \
    #            (+4)
    # (+1) \    /
    #       (+2)
    # (+1) /
    #
    #       (/2)
    #           \
    #            (/4)
    #           /
    #       (/2)
    assert len(handle_map) is 10

    snapshot.assert_match(result.data)
