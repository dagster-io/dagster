from pathlib import Path

import pytest
from dagster_shared.serdes.objects import LibraryEntryKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", LibraryEntryKey("foo", "bar")),
        ("foo.Bar", LibraryEntryKey("foo", "Bar")),
        ("foo.bar.baz", LibraryEntryKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: LibraryEntryKey) -> None:
    assert LibraryEntryKey.from_typename(typename) == key


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
        LibraryEntryKey.from_typename(typename)
