import pytest
from dagster._check import ParameterCheckError
from dagster._core.definitions.data_version import DataVersion


def test_logical_version_construction():
    ver = DataVersion("foo")
    assert ver.value == "foo"

    with pytest.raises(ParameterCheckError):
        DataVersion(100)


def test_logical_version_equality():
    assert DataVersion("foo") == DataVersion("foo")
