from dagster.utils import file_relative_path
from dagster.utils.yaml_utils import (
    load_yaml_from_glob_list,
    load_yaml_from_globs,
    load_yaml_from_path,
)


def test_load_yaml():
    assert load_yaml_from_path(file_relative_path(__file__, 'yamls/yaml_one.yaml')) == {
        'key_one': {'key_one_one': 'value_one'}
    }


def test_from_glob_list():
    assert load_yaml_from_glob_list([file_relative_path(__file__, 'yamls/yaml_one.yaml')]) == {
        'key_one': {'key_one_one': 'value_one'}
    }

    assert load_yaml_from_glob_list(
        [
            file_relative_path(__file__, 'yamls/yaml_one.yaml'),
            file_relative_path(__file__, 'yamls/yaml_two.yaml'),
        ]
    ) == {'key_one': {'key_one_one': 'value_one', 'key_one_two': 'value_two'}}

    assert load_yaml_from_glob_list([file_relative_path(__file__, 'yamls/*.yaml')]) == {
        'key_one': {'key_one_one': 'value_one', 'key_one_two': 'value_two'}
    }

    assert load_yaml_from_globs(
        file_relative_path(__file__, 'yamls/yaml_one.yaml'),
        file_relative_path(__file__, 'yamls/yaml_two.yaml'),
    ) == {'key_one': {'key_one_one': 'value_one', 'key_one_two': 'value_two'}}

    assert load_yaml_from_glob_list(['flskhfhjsdf']) == {}
