import datetime
import os

import pytest
import yaml

import dagster._check as check
from dagster._utils import file_relative_path
from dagster._utils.yaml_utils import (
    dump_run_config_yaml,
    load_run_config_yaml,
    load_yaml_from_glob_list,
    load_yaml_from_globs,
    load_yaml_from_path,
    merge_yaml_strings,
    merge_yamls,
)


def test_load_yaml():
    assert load_yaml_from_path(file_relative_path(__file__, "yamls/yaml_one.yaml")) == {
        "key_one": {"key_one_one": "value_one"}
    }


def test_from_glob_list():
    assert load_yaml_from_glob_list([file_relative_path(__file__, "yamls/yaml_one.yaml")]) == {
        "key_one": {"key_one_one": "value_one"}
    }

    assert load_yaml_from_glob_list(
        [
            file_relative_path(__file__, "yamls/yaml_one.yaml"),
            file_relative_path(__file__, "yamls/yaml_two.yaml"),
        ]
    ) == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}

    assert load_yaml_from_glob_list([file_relative_path(__file__, "yamls/*.yaml")]) == {
        "key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}
    }

    assert load_yaml_from_globs(
        file_relative_path(__file__, "yamls/yaml_one.yaml"),
        file_relative_path(__file__, "yamls/yaml_two.yaml"),
    ) == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}

    assert load_yaml_from_glob_list(["flskhfhjsdf"]) == {}


def test_merge_yamls():
    assert merge_yamls(
        [
            file_relative_path(__file__, os.path.join("yamls", "yaml_one.yaml")),
            file_relative_path(__file__, os.path.join("yamls", "yaml_two.yaml")),
        ]
    ) == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}

    with pytest.raises(
        check.CheckError,
        match=(
            "Expected YAML from file .* to parse to dictionary, "
            'instead got: "this is a valid YAML string but not a dictionary"'
        ),
    ):
        merge_yamls(
            [
                file_relative_path(__file__, os.path.join("yamls", "yaml_one.yaml")),
                file_relative_path(__file__, os.path.join("yamls", "bad", "a_string.yaml")),
            ]
        )


def test_merge_yaml_strings():
    a = """
foo:
  bar: 1
baz: 3
"""
    b = """
foo:
  one: "one"
other: 4
"""
    c = """
final: "result"
"""

    assert merge_yaml_strings([a, b, c]) == {
        "final": "result",
        "foo": {"one": "one", "bar": 1},
        "other": 4,
        "baz": 3,
    }

    override = '''final: "some other result"'''
    assert merge_yaml_strings([a, b, c, override]) == {
        "foo": {"bar": 1, "one": "one"},
        "baz": 3,
        "other": 4,
        "final": "some other result",
    }

    string_yaml = "this is a valid YAML string but not a dictionary"
    expected = 'Expected YAML dictionary, instead got: "{string_yaml}"'.format(
        string_yaml=string_yaml
    )

    with pytest.raises(check.CheckError, match=expected):
        merge_yaml_strings([a, string_yaml])

    with pytest.raises(
        yaml.YAMLError,
        match="while scanning for the next token\nfound character '`' that cannot start any token",
    ):
        bad_yaml = "--- `"
        merge_yaml_strings([a, bad_yaml])


def test_dump_octal_string():

    octal_str_list = {"keys": ["0001823", "0001234"]}

    # normal dump parses the first string as an int
    assert yaml.safe_dump(octal_str_list) == "keys:\n- 0001823\n- '0001234'\n"

    # our dump does not
    assert dump_run_config_yaml(octal_str_list) == "keys:\n- '0001823'\n- '0001234'\n"


def test_load_datetime_string():
    date_config_yaml = """ops:
  my_op:
    config:
      start: 2022-06-10T00:00:00.000000+00:00"""

    # normal dump parses as a datetime
    assert yaml.safe_load(date_config_yaml) == {
        "ops": {
            "my_op": {
                "config": {
                    "start": datetime.datetime(2022, 6, 10, 0, 0, tzinfo=datetime.timezone.utc)
                }
            }
        }
    }

    # ours does not
    assert load_run_config_yaml(date_config_yaml) == {
        "ops": {"my_op": {"config": {"start": "2022-06-10T00:00:00.000000+00:00"}}}
    }
