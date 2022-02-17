import inspect
import re

import dagster
import pytest


def test_all():
    dagster_dir = dir(dagster)
    for each in dagster.__all__:
        assert each in dagster_dir
    for exported in dagster_dir:
        if (
            not exported.startswith("_")
            and not inspect.ismodule(getattr(dagster, exported))
            and not exported in dagster._DEPRECATED
        ):
            assert exported in dagster.__all__


def test_deprecated_imports(monkeypatch):
    Bar = object()

    monkeypatch.setattr(dagster, "_DEPRECATED", {"Foo": ("Bar", Bar, "0.0.0")}, raising=True)
    with pytest.warns(DeprecationWarning, match=re.escape('"Foo" is deprecated')):
        from dagster import Foo  # pylint: disable=no-name-in-module

    assert Foo is Bar
