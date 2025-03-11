from pathlib import Path

import pytest
from dagster_shared.serdes.objects import LibraryObjectKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", LibraryObjectKey("foo", "bar")),
        ("foo.Bar", LibraryObjectKey("foo", "Bar")),
        ("foo.bar.baz", LibraryObjectKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: LibraryObjectKey) -> None:
    assert LibraryObjectKey.from_typename(typename) == key


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
        LibraryObjectKey.from_typename(typename)
