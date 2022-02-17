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

    # Using `EventMetadataEntry` as a standin for the rest since monkeypatch does not work on 3.6
    from dagster import MetadataEntry

    with pytest.warns(DeprecationWarning, match=re.escape('"EventMetadataEntry" is deprecated')):
        from dagster import EventMetadataEntry  # pylint: disable=no-name-in-module

    assert EventMetadataEntry is MetadataEntry
