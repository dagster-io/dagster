from dagster_graphql.test.utils import execute_dagster_graphql

from .composites_query import (
    COMPOSITES_QUERY,
    COMPOSITES_QUERY_NESTED_DEPENDS_ON_DEPENDS_BY_CORE,
    NESTED_INPUT_DEPENDS_ON,
    NESTED_OUTPUT_DEPENDED_BY,
    PARENT_ID_QUERY,
    SOLID_ID_QUERY,
)
from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix

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


# this only needs readonly variants since they never execute anything
class TestComposites(ReadonlyGraphQLContextTestMatrix):
    def test_composites(self, graphql_context, snapshot):
        result = execute_dagster_graphql(graphql_context, COMPOSITES_QUERY)
        handle_map = {}

        for obj in result.data['pipelineOrError']['solidHandles']:
            handle_map[obj['handleID']] = obj['solid']

        assert len(handle_map) == 10

        snapshot.assert_match(result.data)

    def test_parent_id_arg(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, PARENT_ID_QUERY, {})
        assert len(result.data['pipelineOrError']['solidHandles']) == 10

        result = execute_dagster_graphql(graphql_context, PARENT_ID_QUERY, {'parentHandleID': ''})
        assert len(result.data['pipelineOrError']['solidHandles']) == 2

        result = execute_dagster_graphql(
            graphql_context, PARENT_ID_QUERY, {'parentHandleID': 'add_four'}
        )
        assert len(result.data['pipelineOrError']['solidHandles']) == 2

        result = execute_dagster_graphql(
            graphql_context, PARENT_ID_QUERY, {'parentHandleID': 'add_four.adder_1'}
        )
        assert len(result.data['pipelineOrError']['solidHandles']) == 2

        result = execute_dagster_graphql(
            graphql_context, PARENT_ID_QUERY, {'parentHandleID': 'add_four.doot'}
        )
        assert len(result.data['pipelineOrError']['solidHandles']) == 0

    def test_solid_id(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, SOLID_ID_QUERY, {'id': 'add_four'})
        assert result.data['pipelineOrError']['solidHandle']['handleID'] == 'add_four'

        result = execute_dagster_graphql(
            graphql_context, SOLID_ID_QUERY, {'id': 'add_four.adder_1.adder_1'}
        )
        assert (
            result.data['pipelineOrError']['solidHandle']['handleID'] == 'add_four.adder_1.adder_1'
        )

        result = execute_dagster_graphql(graphql_context, SOLID_ID_QUERY, {'id': 'bonkahog'})
        assert result.data['pipelineOrError']['solidHandle'] == None

    def test_recurse_composites_depends(self, graphql_context):
        execute_dagster_graphql(
            graphql_context,
            COMPOSITES_QUERY_NESTED_DEPENDS_ON_DEPENDS_BY_CORE + NESTED_INPUT_DEPENDS_ON,
        )

        execute_dagster_graphql(
            graphql_context,
            COMPOSITES_QUERY_NESTED_DEPENDS_ON_DEPENDS_BY_CORE + NESTED_OUTPUT_DEPENDED_BY,
        )
