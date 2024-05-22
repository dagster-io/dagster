import pytest
from dagster import AssetKey, AssetMaterialization, TableColumn, TableSchema
from dagster._check import CheckError
from dagster._core.definitions.tags import NamespacedTagSet
from dagster._core.test_utils import ignore_warning, raise_exception_on_warnings


def test_invalid_tag_set() -> None:
    class MyJunkTagSet(NamespacedTagSet):
        junk: int

        @classmethod
        def namespace(cls) -> str:
            return "dagster"

    with pytest.raises(CheckError):
        MyJunkTagSet(junk=1)
