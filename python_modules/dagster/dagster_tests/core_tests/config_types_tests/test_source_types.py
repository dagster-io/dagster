import os

from dagster import Array, BoolSource, IntSource, Noneable, StringSource
from dagster._config import process_config
from dagster._core.test_utils import environ


def test_string_source():
    assert process_config(StringSource, "foo").success  # pyright: ignore[reportArgumentType]
    assert not process_config(StringSource, 1).success  # pyright: ignore[reportArgumentType]

    assert not process_config(StringSource, {"env": 1}).success

    assert "DAGSTER_TEST_ENV_VAR" not in os.environ
    assert not process_config(StringSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success

    assert (
        'You have attempted to fetch the environment variable "DAGSTER_TEST_ENV_VAR" '
        "which is not set. In order for this execution to succeed it must be set in "
        "this environment."
        in process_config(StringSource, {"env": "DAGSTER_TEST_ENV_VAR"}).errors[0].message  # pyright: ignore[reportOptionalSubscript]
    )

    with environ({"DAGSTER_TEST_ENV_VAR": "baz"}):
        assert process_config(StringSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success
        assert process_config(StringSource, {"env": "DAGSTER_TEST_ENV_VAR"}).value == "baz"


def test_int_source():
    assert process_config(IntSource, 1).success  # pyright: ignore[reportArgumentType]
    assert not process_config(IntSource, "foo").success  # pyright: ignore[reportArgumentType]

    assert not process_config(IntSource, {"env": 1}).success

    assert "DAGSTER_TEST_ENV_VAR" not in os.environ
    assert not process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success

    assert (
        'You have attempted to fetch the environment variable "DAGSTER_TEST_ENV_VAR" '
        "which is not set. In order for this execution to succeed it must be set in "
        "this environment."
        in process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).errors[0].message  # pyright: ignore[reportOptionalSubscript]
    )

    with environ({"DAGSTER_TEST_ENV_VAR": "4"}):
        assert process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success
        assert process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).value == 4

    with environ({"DAGSTER_TEST_ENV_VAR": "four"}):
        assert not process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success
        assert (
            'Value "four" stored in env variable "DAGSTER_TEST_ENV_VAR" cannot '
            "be coerced into an int."
            in process_config(IntSource, {"env": "DAGSTER_TEST_ENV_VAR"}).errors[0].message  # pyright: ignore[reportOptionalSubscript]
        )


def test_noneable_string_source_array():
    assert process_config(Noneable(Array(StringSource)), []).success  # pyright: ignore[reportArgumentType]
    assert process_config(Noneable(Array(StringSource)), None).success  # pyright: ignore[reportArgumentType]
    assert (
        'You have attempted to fetch the environment variable "DAGSTER_TEST_ENV_VAR" '
        "which is not set. In order for this execution to succeed it must be set in "
        "this environment."
        in process_config(Noneable(Array(StringSource)), ["test", {"env": "DAGSTER_TEST_ENV_VAR"}])  # pyright: ignore[reportArgumentType,reportOptionalSubscript]
        .errors[0]
        .message
    )

    with environ({"DAGSTER_TEST_ENV_VAR": "baz"}):
        assert process_config(
            Noneable(Array(StringSource)),
            ["test", {"env": "DAGSTER_TEST_ENV_VAR"}],  # pyright: ignore[reportArgumentType]
        ).success


def test_bool_source():
    assert process_config(BoolSource, True).success  # pyright: ignore[reportArgumentType]
    assert process_config(BoolSource, False).success  # pyright: ignore[reportArgumentType]
    assert not process_config(BoolSource, "False").success  # pyright: ignore[reportArgumentType]
    assert not process_config(BoolSource, "foo").success  # pyright: ignore[reportArgumentType]
    assert not process_config(BoolSource, 1).success  # pyright: ignore[reportArgumentType]

    assert not process_config(BoolSource, {"env": 1}).success

    assert "DAGSTER_TEST_ENV_VAR" not in os.environ
    assert not process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success

    assert (
        'You have attempted to fetch the environment variable "DAGSTER_TEST_ENV_VAR" '
        "which is not set. In order for this execution to succeed it must be set in "
        "this environment."
        in process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).errors[0].message  # pyright: ignore[reportOptionalSubscript]
    )

    with environ({"DAGSTER_TEST_ENV_VAR": ""}):
        assert process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success
        assert process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).value is False

    with environ({"DAGSTER_TEST_ENV_VAR": "True"}):
        assert process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).success
        assert process_config(BoolSource, {"env": "DAGSTER_TEST_ENV_VAR"}).value is True
