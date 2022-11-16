import pytest

from dagster._check import ParameterCheckError
from dagster._core.definitions.logical_version import LogicalVersion


def test_logical_version_construction():
    ver = LogicalVersion("foo")
    assert ver.value == "foo"

    with pytest.raises(ParameterCheckError):
        LogicalVersion(100)


def test_logical_version_equality():
    assert LogicalVersion("foo") == LogicalVersion("foo")
