import os

import pytest
import yaml
from dagster import check
from dagster.utils import file_relative_path
from dagster.utils.yaml_utils import (
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

    assert (
        load_yaml_from_glob_list(
            [
                file_relative_path(__file__, "yamls/yaml_one.yaml"),
                file_relative_path(__file__, "yamls/yaml_two.yaml"),
            ]
        )
        == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}
    )

    assert load_yaml_from_glob_list([file_relative_path(__file__, "yamls/*.yaml")]) == {
        "key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}
    }

    assert (
        load_yaml_from_globs(
            file_relative_path(__file__, "yamls/yaml_one.yaml"),
            file_relative_path(__file__, "yamls/yaml_two.yaml"),
        )
        == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}
    )

    assert load_yaml_from_glob_list(["flskhfhjsdf"]) == {}


def test_merge_yamls():
    assert (
        merge_yamls(
            [
                file_relative_path(__file__, os.path.join("yamls", "yaml_one.yaml")),
                file_relative_path(__file__, os.path.join("yamls", "yaml_two.yaml")),
            ]
        )
        == {"key_one": {"key_one_one": "value_one", "key_one_two": "value_two"}}
    )

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
