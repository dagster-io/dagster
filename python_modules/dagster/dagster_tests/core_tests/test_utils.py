import warnings

import pytest

import dagster.version
from dagster._core.test_utils import environ
from dagster._core.utils import check_dagster_package_version, parse_env_var


def test_parse_env_var_no_equals():

    env_var = "FOO_ENV_VAR"

    with pytest.raises(
        Exception, match="Tried to load environment variable FOO_ENV_VAR, but it was not set"
    ):
        parse_env_var(env_var)

    with environ({"FOO_ENV_VAR": "BAR_VALUE"}):
        assert parse_env_var(env_var) == ("FOO_ENV_VAR", "BAR_VALUE")


def test_parse_env_var_equals():
    env_var = "FOO_ENV_VAR=BAR_VALUE"
    assert parse_env_var(env_var) == ("FOO_ENV_VAR", "BAR_VALUE")


def test_parse_env_var_containing_equals():
    env_var = "FOO_ENV_VAR=HERE_COMES_THE_EQUALS=THERE_IT_WENT"

    assert parse_env_var(env_var) == ("FOO_ENV_VAR", "HERE_COMES_THE_EQUALS=THERE_IT_WENT")


def test_check_dagster_package_version(monkeypatch):

    monkeypatch.setattr(dagster.version, "__version__", "1.1.0")

    # Ensure no warning emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_dagster_package_version("foo", "1.1.0")

    # Lib version matching 1.1.0-- see dagster._utils.library_version_from_core_version
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_dagster_package_version("foo", "0.17.0")

    with pytest.warns():
        check_dagster_package_version("foo", "1.0.0")

    with pytest.warns():
        check_dagster_package_version("foo", "0.16.5")
