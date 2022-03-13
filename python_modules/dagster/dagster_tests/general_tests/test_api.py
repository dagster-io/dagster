import importlib
import inspect
import pkgutil
import re

import pytest

import dagster


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
    with pytest.warns(DeprecationWarning, match=re.escape('"EventMetadataEntry" is deprecated')):
        from dagster import EventMetadataEntry, MetadataEntry
    assert EventMetadataEntry is MetadataEntry


def test_deprecated_top_level_submodule_import():

    # one hardcoded
    assert importlib.import_module("dagster.core") == importlib.import_module("dagster._core")

    exclude_submodules = ["_module_alias_map"]

    # all top level private (single-underscore prefix) submodule
    private_submodules = [
        p.name
        for p in pkgutil.iter_modules(dagster.__path__)
        if re.match(r"^_[^_]", p.name) and not p.name in exclude_submodules
    ]
    for submodule in private_submodules:
        assert importlib.import_module(f"dagster.{submodule}") == importlib.import_module(
            f"dagster.{submodule[1:]}"  # strip the leading underscore
        )


def test_deprecated_nested_submodule_import():
    assert importlib.import_module("dagster.core.definitions") == importlib.import_module(
        "dagster._core.definitions"
    )
