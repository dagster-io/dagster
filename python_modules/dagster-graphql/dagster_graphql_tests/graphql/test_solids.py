from dagster_graphql.test.utils import execute_dagster_graphql


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


def test_query_all_solids(graphql_context, snapshot):
    result = execute_dagster_graphql(graphql_context, all_solids_query())
    snapshot.assert_match(result.data)


def test_query_get_solid_exists(graphql_context):
    result = execute_dagster_graphql(graphql_context, get_solid_query_exists())

    assert not result.errors
    assert result.data['usedSolid']['definition']['name'] == 'sum_solid'
