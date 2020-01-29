from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context


def test_query_all_solids(snapshot):
    query = '{ usedSolids { __typename, definition { name }, invocations { pipeline { name }, solidHandle { handleID } } } }'
    result = execute_dagster_graphql(define_test_context(), query)
    snapshot.assert_match(result.data)
