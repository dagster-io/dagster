from .setup import execute_dagster_graphql, define_context


def execute_preset_query(pipeline_name):
    pipeline_query = '''
        query PresetsQuery($name: String!) {
            pipeline(params: { name: $name }) {
                presets {
                    __typename
                    name
                    solidSubset
                    environment
                }
            }
        }
    '''

    return execute_dagster_graphql(
        define_context(), pipeline_query, variables={'name': pipeline_name}
    )


def test_basic_preset_query_no_presets():
    result = execute_preset_query('csv_hello_world_two')
    assert result.data == {'pipeline': {'presets': []}}


def test_basic_preset_query_with_presets(snapshot):
    result = execute_preset_query('csv_hello_world')

    assert [preset_data['name'] for preset_data in result.data['pipeline']['presets']] == [
        'prod',
        'test',
    ]

    snapshot.assert_match(result.data)
