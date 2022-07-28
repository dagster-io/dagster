import importlib
import inspect
import re
import sys

import pytest

import dagster
from dagster._module_alias_map import AliasedModuleFinder, get_meta_path_insertion_index


def test_all():
    dagster_dir = dir(dagster)
    for each in dagster.__all__:
        assert each in dagster_dir
    for exported in dagster_dir:
        if (
            not exported.startswith("_")
            and not inspect.ismodule(getattr(dagster, exported))
            and not exported in dagster._DEPRECATED  # pylint: disable=protected-access
        ):
            assert exported in dagster.__all__


def test_deprecated_imports():
    with pytest.warns(
        DeprecationWarning, match=re.escape("dagster_type_materializer is deprecated")
    ):
        from dagster import dagster_type_materializer  # pylint: disable=unused-import
    with pytest.warns(DeprecationWarning, match=re.escape("DagsterTypeMaterializer is deprecated")):
        from dagster import DagsterTypeMaterializer  # pylint: disable=unused-import


@pytest.fixture
def patch_sys_meta_path():
    aliased_finder = AliasedModuleFinder({"dagster.foo": "dagster.core"})
    sys.meta_path.insert(get_meta_path_insertion_index(), aliased_finder)
    yield
    sys.meta_path.remove(aliased_finder)


@pytest.mark.usefixtures("patch_sys_meta_path")
def test_aliased_module_finder_import():
    assert importlib.import_module("dagster.foo") == importlib.import_module("dagster.core")


@pytest.mark.usefixtures("patch_sys_meta_path")
def test_aliased_module_finder_nested_import():
    assert importlib.import_module("dagster.foo.definitions") == importlib.import_module(
        "dagster.core.definitions"
    )


def test_deprecated_top_level_submodule_import():
    assert importlib.import_module("dagster.check") == importlib.import_module("dagster._check")
