from dagster_components.lib.custom_component import get_custom_component_template


def test_custom_component_template() -> None:
    source_from_fn = get_custom_component_template("Foo", "foo")

    assert "class FooComponent" in source_from_fn
