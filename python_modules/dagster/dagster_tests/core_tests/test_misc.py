import pytest
from dagster.core.definitions.utils import (
    check_valid_name,
    config_from_files,
    config_from_pkg_resources,
    config_from_yaml_strings,
)
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import file_relative_path


def test_check_valid_name():
    assert check_valid_name("a") == "a"

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name("has a space")

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name("")

    with pytest.raises(DagsterInvalidDefinitionError):
        assert check_valid_name("context")


def test_config_from_files():
    run_config = config_from_files(
        config_files=[file_relative_path(__file__, "./definitions_tests/pass_env.yaml")]
    )

    assert run_config == {"solids": {"can_fail": {"config": {"error": False}}}}

    with pytest.raises(DagsterInvariantViolationError):
        config_from_files(config_files=[file_relative_path(__file__, "not_a_file.yaml")])

    with pytest.raises(DagsterInvariantViolationError):
        config_from_files(
            config_files=[
                file_relative_path(__file__, "./definitions_tests/test_repository_definition.py")
            ]
        )


def test_config_from_yaml_strings():
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

    run_config = config_from_yaml_strings([a, b, c])
    assert run_config == {
        "foo": {"bar": 1, "one": "one"},
        "baz": 3,
        "other": 4,
        "final": "result",
    }

    with pytest.raises(
        DagsterInvariantViolationError, match="Encountered error attempting to parse yaml"
    ):
        config_from_yaml_strings(["--- `"])

    run_config = config_from_yaml_strings([])
    assert run_config == {}


def test_config_from_pkg_resources():
    good = (
        "dagster_tests.core_tests.definitions_tests",
        "pass_env.yaml",
    )
    run_config = config_from_pkg_resources([good])
    assert run_config == {"solids": {"can_fail": {"config": {"error": False}}}}

    bad_defs = [
        ("dagster_tests.core_tests.definitions_tests", "does_not_exist.yaml"),
        (
            "dagster_tests.core_tests.definitions_tests",
            "bad_file_binary.yaml",
        ),
    ]

    for bad_def in bad_defs:
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Encountered error attempting to parse yaml",
        ):
            config_from_pkg_resources([bad_def])
