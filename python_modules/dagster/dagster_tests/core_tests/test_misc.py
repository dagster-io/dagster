import dagster as dg
import pytest
from dagster._core.definitions.utils import check_valid_name


def test_check_valid_name():
    assert check_valid_name("a") == "a"

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        assert check_valid_name("has a space")

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        assert check_valid_name("")

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        assert check_valid_name("context")


def test_config_from_files():
    run_config = dg.config_from_files(
        config_files=[dg.file_relative_path(__file__, "../definitions_tests/pass_env.yaml")]
    )

    assert run_config == {"ops": {"can_fail": {"config": {"error": False}}}}

    with pytest.raises(dg.DagsterInvariantViolationError):
        dg.config_from_files(config_files=[dg.file_relative_path(__file__, "not_a_file.yaml")])

    with pytest.raises(dg.DagsterInvariantViolationError):
        dg.config_from_files(
            config_files=[
                dg.file_relative_path(__file__, "./definitions_tests/test_repository_definition.py")
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

    run_config = dg.config_from_yaml_strings([a, b, c])
    assert run_config == {
        "foo": {"bar": 1, "one": "one"},
        "baz": 3,
        "other": 4,
        "final": "result",
    }

    with pytest.raises(
        dg.DagsterInvariantViolationError, match="Encountered error attempting to parse yaml"
    ):
        dg.config_from_yaml_strings(["--- `"])

    run_config = dg.config_from_yaml_strings([])
    assert run_config == {}


def test_config_from_pkg_resources():
    good = (
        "dagster_tests.definitions_tests",
        "pass_env.yaml",
    )
    run_config = dg.config_from_pkg_resources([good])
    assert run_config == {"ops": {"can_fail": {"config": {"error": False}}}}

    bad_defs = [
        ("dagster_tests.definitions_tests", "does_not_exist.yaml"),
        (
            "dagster_tests.definitions_tests",
            "bad_file_binary.yaml",
        ),
    ]

    for bad_def in bad_defs:
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match="Encountered error attempting to parse yaml",
        ):
            dg.config_from_pkg_resources([bad_def])


def test_bk_runs():
    # hi there
    assert True
