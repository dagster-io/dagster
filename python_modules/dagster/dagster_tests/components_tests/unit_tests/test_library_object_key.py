from pathlib import Path

import pytest
from dagster_shared.serdes.objects import PackageObjectKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", PackageObjectKey("foo", "bar")),
        ("foo.Bar", PackageObjectKey("foo", "Bar")),
        ("foo.bar.baz", PackageObjectKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: PackageObjectKey) -> None:
    assert PackageObjectKey.from_typename(typename) == key


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
        PackageObjectKey.from_typename(typename)
