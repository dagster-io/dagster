from dagster.utils.merger import dict_merge


def test_simple_merge():
    assert dict_merge({}, {}) == {}
    assert dict_merge({1: 2}, {}) == {1: 2}
    assert dict_merge({}, {1: 2}) == {1: 2}


def test_nested_merge():
    from_dict = {'key': {'nested_one': 1}}

    onto_dict = {'key': {'nested_two': 2}}

    assert dict_merge(from_dict, onto_dict) == {'key': {'nested_one': 1, 'nested_two': 2}}


def test_smash():
    from_dict = {'value': 'smasher'}
    onto_dict = {'value': 'got_smashed'}

    assert dict_merge(from_dict, onto_dict)['value'] == 'smasher'


def test_realistic():
    from_dict = {
        'context': {
            'unittest': {
                'resources': {
                    'db_resource': {'config': {'user': 'some_user', 'password': 'some_password'}}
                }
            }
        }
    }

    onto_dict = {'context': {'unittest': {'resources': {'another': {'config': 'not_sensitive'}}}}}

    result_dict = {
        'context': {
            'unittest': {
                'resources': {
                    'db_resource': {'config': {'user': 'some_user', 'password': 'some_password'}},
                    'another': {'config': 'not_sensitive'},
                }
            }
        }
    }

    assert dict_merge(from_dict, onto_dict) == result_dict
