import inspect
from pathlib import Path

import pytest
from dagster_components.core.component_key import ComponentKey


def test_component_key_synced() -> None:
    """Because these modules cannot share a dependency outside of tests, we rely on a janky unit test
    to make sure their definitions remain in sync.
    """
    import dagster_components.core.component_key as dagster_components_component_key
    import dagster_dg.component_key as dagster_dg_component_key

    assert inspect.getsource(dagster_components_component_key) == inspect.getsource(
        dagster_dg_component_key
    )


dirpath = Path(".")


@pytest.mark.parametrize(
    ["component_typename", "component_key"],
    [
        ("foo.bar", ComponentKey("foo", "bar")),
        ("foo.Bar", ComponentKey("foo", "Bar")),
        ("foo.bar.baz", ComponentKey("foo.bar", "baz")),
    ],
)
def test_valid_component_keys(component_typename: str, component_key: ComponentKey) -> None:
    assert ComponentKey.from_typename(component_typename) == component_key


@pytest.mark.parametrize(
    "component_typename",
    [
        "foo",
        "foo@bar",
        ".foo.bar",
    ],
)
def test_invalid_component_keys(component_typename: str) -> None:
    with pytest.raises(ValueError):
        ComponentKey.from_typename(component_typename)
