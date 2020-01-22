from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context

COMPOSITES_QUERY = '''
query CompositesQuery {
  pipeline(params: { name: "composites_pipeline" }) {
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

PARENT_ID_QUERY = '''
query withParent($parentHandleID: String) {
  pipeline(params: { name: "composites_pipeline" }) {
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
  pipeline(params: { name: "composites_pipeline" }) {
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


def test_composites(snapshot):
    result = execute_dagster_graphql(define_test_context(), COMPOSITES_QUERY)
    handle_map = {}

    for obj in result.data["pipeline"]["solidHandles"]:
        handle_map[obj["handleID"]] = obj["solid"]

    assert len(handle_map) == 10

    snapshot.assert_match(result.data)


def test_parent_id_arg():
    result = execute_dagster_graphql(define_test_context(), PARENT_ID_QUERY, {})
    assert len(result.data["pipeline"]["solidHandles"]) == 10

    result = execute_dagster_graphql(define_test_context(), PARENT_ID_QUERY, {'parentHandleID': ''})
    assert len(result.data["pipeline"]["solidHandles"]) == 2

    result = execute_dagster_graphql(
        define_test_context(), PARENT_ID_QUERY, {'parentHandleID': 'add_four'}
    )
    assert len(result.data["pipeline"]["solidHandles"]) == 2

    result = execute_dagster_graphql(
        define_test_context(), PARENT_ID_QUERY, {'parentHandleID': 'add_four.adder_1'}
    )
    assert len(result.data["pipeline"]["solidHandles"]) == 2

    result = execute_dagster_graphql(
        define_test_context(), PARENT_ID_QUERY, {'parentHandleID': 'add_four.doot'}
    )
    assert len(result.data["pipeline"]["solidHandles"]) == 0


def test_solid_id():
    result = execute_dagster_graphql(define_test_context(), SOLID_ID_QUERY, {'id': 'add_four'})
    assert result.data["pipeline"]["solidHandle"]["handleID"] == 'add_four'

    result = execute_dagster_graphql(
        define_test_context(), SOLID_ID_QUERY, {'id': 'add_four.adder_1.adder_1'}
    )
    assert result.data["pipeline"]["solidHandle"]["handleID"] == 'add_four.adder_1.adder_1'

    result = execute_dagster_graphql(define_test_context(), SOLID_ID_QUERY, {'id': 'bonkahog'})
    assert result.data["pipeline"]["solidHandle"] == None
