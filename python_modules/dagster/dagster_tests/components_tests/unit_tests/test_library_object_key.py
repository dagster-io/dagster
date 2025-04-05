from pathlib import Path

import pytest
from dagster_shared.serdes.objects import PackageEntryKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", PackageEntryKey("foo", "bar")),
        ("foo.Bar", PackageEntryKey("foo", "Bar")),
        ("foo.bar.baz", PackageEntryKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: PackageEntryKey) -> None:
    assert PackageEntryKey.from_typename(typename) == key


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
        PackageEntryKey.from_typename(typename)
