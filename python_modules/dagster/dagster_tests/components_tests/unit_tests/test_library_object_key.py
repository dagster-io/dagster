from pathlib import Path

import pytest
from dagster_shared.serdes.objects import DgRegistryKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", DgRegistryKey("foo", "bar")),
        ("foo.Bar", DgRegistryKey("foo", "Bar")),
        ("foo.bar.baz", DgRegistryKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: DgRegistryKey) -> None:
    assert DgRegistryKey.from_typename(typename) == key


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
        DgRegistryKey.from_typename(typename)
