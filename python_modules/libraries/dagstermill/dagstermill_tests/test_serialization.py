import pytest
from dagster import Any, String, usable_as_dagster_type
from dagster.check import CheckError
from dagster.core.types.dagster_type import resolve_dagster_type
from dagster.utils import safe_tempfile_path
from dagstermill.serialize import read_value, write_value


def test_scalar():
    with safe_tempfile_path() as tempfile_path:
        assert (
            read_value(
                resolve_dagster_type(String),
                write_value(resolve_dagster_type(String), "foo", tempfile_path),
            )
            == "foo"
        )


def test_scalar_any():
    with safe_tempfile_path() as tempfile_path:
        assert (
            read_value(
                resolve_dagster_type(Any),
                write_value(resolve_dagster_type(Any), "foo", tempfile_path),
            )
            == "foo"
        )


@usable_as_dagster_type
class EvenType:
    def __init__(self, num):
        assert num % 2 is 0
        self.num = num


def test_custom_dagster_type():
    with safe_tempfile_path() as tempfile_path:
        assert (
            read_value(
                resolve_dagster_type(EvenType),
                write_value(resolve_dagster_type(EvenType), 4, tempfile_path),
            )
            == 4
        )


def test_read_bad_value():
    with pytest.raises(CheckError, match="Malformed value"):
        read_value(resolve_dagster_type(Any), {"value": "foo", "file": "bar"})
    with pytest.raises(CheckError, match="Malformed value"):
        read_value(resolve_dagster_type(Any), {"quux": "buzz"})
