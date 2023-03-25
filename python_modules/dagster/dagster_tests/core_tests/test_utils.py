import warnings
from typing import Dict, List, NamedTuple

import dagster.version
import pytest
from dagster._core.libraries import DagsterLibraryRegistry
from dagster._core.test_utils import environ
from dagster._core.utils import check_dagster_package_version, parse_env_var
from dagster._utils import hash_collection, library_version_from_core_version


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

    with pytest.warns(Warning):  # minor version
        check_dagster_package_version("foo", "1.2.0")

    with pytest.warns(Warning):  # patch version
        check_dagster_package_version("foo", "1.1.1")

    with pytest.warns(Warning):  # minor version
        check_dagster_package_version("foo", "0.18.0")

    with pytest.warns(Warning):  # patch version
        check_dagster_package_version("foo", "0.17.1")


def test_library_version_from_core_version():
    assert library_version_from_core_version("1.1.16") == "0.17.16"
    assert library_version_from_core_version("0.17.16") == "0.17.16"
    assert library_version_from_core_version("1.1.16pre0") == "0.17.16rc0"
    assert library_version_from_core_version("1.1.16rc0") == "0.17.16rc0"
    assert library_version_from_core_version("1.1.16post0") == "0.17.16post0"


def test_library_registry():
    assert DagsterLibraryRegistry.get() == {"dagster": dagster.version.__version__}


def test_hash_collection():
    # lists have different hashes depending on order
    assert hash_collection([1, 2, 3]) == hash_collection([1, 2, 3])
    assert hash_collection([1, 2, 3]) != hash_collection([2, 1, 3])

    # dicts have same hash regardless of order
    assert hash_collection({"a": 1, "b": 2}) == hash_collection({"b": 2, "a": 1})

    assert hash_collection(set(range(10))) == hash_collection(set(range(10)))

    with pytest.raises(AssertionError):
        hash_collection(object())

    class Foo(NamedTuple):
        a: List[int]
        b: Dict[str, int]
        c: str

    with pytest.raises(Exception):
        hash(Foo([1, 2, 3], {"a": 1}, "alpha"))

    class Bar(Foo):
        def __hash__(self):
            return hash_collection(self)

    assert hash(Bar([1, 2, 3], {"a": 1}, "alpha")) == hash(Bar([1, 2, 3], {"a": 1}, "alpha"))
