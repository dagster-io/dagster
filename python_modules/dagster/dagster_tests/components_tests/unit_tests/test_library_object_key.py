from pathlib import Path

import pytest
from dagster_shared.serdes.objects import PluginObjectKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", PluginObjectKey("foo", "bar")),
        ("foo.Bar", PluginObjectKey("foo", "Bar")),
        ("foo.bar.baz", PluginObjectKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: PluginObjectKey) -> None:
    assert PluginObjectKey.from_typename(typename) == key


@pytest.mark.parametrize(
    "typename",
    [
        "foo",
        "foo@bar",
        ".foo.bar",
    ],
)
def test_invalid_keys(typename: str) -> None:
    with pytest.raises(ValueError):
        PluginObjectKey.from_typename(typename)
