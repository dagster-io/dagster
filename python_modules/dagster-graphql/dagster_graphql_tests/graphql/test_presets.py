import re
from collections import OrderedDict

from dagster_graphql.test.preset_query import execute_preset_query

from .setup import define_test_context


def test_basic_preset_query_no_presets():
    result = execute_preset_query('csv_hello_world_two', define_test_context())
    assert result.data == OrderedDict(
        [('pipeline', OrderedDict([('name', 'csv_hello_world_two'), ('presets', [])]))]
    )


def test_basic_preset_query_with_presets(snapshot):
    result = execute_preset_query('csv_hello_world', define_test_context())

    assert [preset_data['name'] for preset_data in result.data['pipeline']['presets']] == [
        'prod',
        'test',
        'test_inline',
    ]

    # Remove local filepath from snapshot
    result.data['pipeline']['presets'][2]['environmentConfigYaml'] = re.sub(
        r'num: .*/data/num.csv',
        'num: /data/num.csv',
        result.data['pipeline']['presets'][2]['environmentConfigYaml'],
    )
    snapshot.assert_match(result.data)
