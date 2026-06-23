import dagster as dg
import pytest
from dagster._check import ParameterCheckError


def test_data_version_construction():
    ver = dg.DataVersion("foo")
    assert ver.value == "foo"

    with pytest.raises(ParameterCheckError):
        dg.DataVersion(100)  # ty: ignore[invalid-argument-type]


def test_data_version_equality():
    assert dg.DataVersion("foo") == dg.DataVersion("foo")
