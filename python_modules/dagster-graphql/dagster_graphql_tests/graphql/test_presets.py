from dagster_graphql.test.preset_query import execute_preset_query
from .setup import define_context


def test_basic_preset_query_no_presets():
    result = execute_preset_query('csv_hello_world_two', define_context())
    assert result.data == {'pipeline': {'name': 'csv_hello_world_two', 'presets': []}}


def test_basic_preset_query_with_presets(snapshot):
    result = execute_preset_query('csv_hello_world', define_context())

    assert [preset_data['name'] for preset_data in result.data['pipeline']['presets']] == [
        'prod',
        'test',
    ]

    snapshot.assert_match(result.data)
