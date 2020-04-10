from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context, define_test_snapshot_context


def all_solids_query():
    return '{ usedSolids { __typename, definition { name }, invocations { pipeline { name }, solidHandle { handleID } } } }'


def get_solid_query_exists():
    return '''
    { 
        usedSolid(name: "sum_solid") {
            ... on UsedSolid { definition { name } }
        }
    }
    '''


def test_query_all_solids(snapshot):
    result = execute_dagster_graphql(define_test_context(), all_solids_query())
    snapshot.assert_match(result.data)


def test_query_all_solids_with_snapshot_context(snapshot):
    result = execute_dagster_graphql(define_test_snapshot_context(), all_solids_query(),)
    snapshot.assert_match(result.data)


def test_query_get_solid_exists():
    result = execute_dagster_graphql(define_test_context(), get_solid_query_exists())

    assert not result.errors
    assert result.data['usedSolid']['definition']['name'] == 'sum_solid'


def test_query_get_solid_with_snapshot_context_exists():
    result = execute_dagster_graphql(define_test_snapshot_context(), get_solid_query_exists(),)

    assert not result.errors
    assert result.data['usedSolid']['definition']['name'] == 'sum_solid'
