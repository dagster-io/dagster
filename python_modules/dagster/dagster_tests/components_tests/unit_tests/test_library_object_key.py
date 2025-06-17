from pathlib import Path

import pytest
from dagster_shared.serdes.objects import EnvRegistryKey

dirpath = Path(".")


@pytest.mark.parametrize(
    ["typename", "key"],
    [
        ("foo.bar", EnvRegistryKey("foo", "bar")),
        ("foo.Bar", EnvRegistryKey("foo", "Bar")),
        ("foo.bar.baz", EnvRegistryKey("foo.bar", "baz")),
    ],
)
def test_valid_keys(typename: str, key: EnvRegistryKey) -> None:
    assert EnvRegistryKey.from_typename(typename) == key


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
        EnvRegistryKey.from_typename(typename)
