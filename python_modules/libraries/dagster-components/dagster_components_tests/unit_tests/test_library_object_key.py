import inspect
from pathlib import Path

import pytest
from dagster_components.core.library_object_key import LibraryObjectKey


def test_component_key_synced() -> None:
    """Because these modules cannot share a dependency outside of tests, we rely on a janky unit test
    to make sure their definitions remain in sync.
    """
    import dagster_components.core.library_object_key as dagster_components_key
    import dagster_dg.library_object_key as dagster_dg_key

    assert inspect.getsource(dagster_components_key) == inspect.getsource(dagster_dg_key)


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
