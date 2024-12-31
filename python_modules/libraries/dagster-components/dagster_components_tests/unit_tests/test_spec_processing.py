import pytest
from dagster import AssetKey, AssetSpec, Definitions
from dagster_components.core.dsl_schema import (
    AssetAttributes,
    MergeAttributes,
    ReplaceAttributes,
    TemplatedValueResolver,
)
from pydantic import BaseModel, TypeAdapter


class M(BaseModel):
    asset_attributes: AssetAttributes = []


defs = Definitions(
    assets=[
        AssetSpec("a", group_name="g1"),
        AssetSpec("b", group_name="g2"),
        AssetSpec("c", group_name="g2", tags={"tag": "val"}),
    ],
)


def test_replace_attributes() -> None:
    op = ReplaceAttributes(operation="replace", target="group:g2", tags={"newtag": "newval"})

    newdefs = op.apply(defs, TemplatedValueResolver.default())
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"newtag": "newval"}


def test_merge_attributes() -> None:
    op = MergeAttributes(operation="merge", target="group:g2", tags={"newtag": "newval"})

    newdefs = op.apply(defs, TemplatedValueResolver.default())
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"tag": "val", "newtag": "newval"}


def test_render_attributes_asset_context() -> None:
    op = MergeAttributes(tags={"group_name_tag": "group__{{ asset.group_name }}"})

    newdefs = op.apply(defs, TemplatedValueResolver.default().with_context(foo="theval"))
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {"group_name_tag": "group__g1"}
    assert asset_graph.get(AssetKey("b")).tags == {"group_name_tag": "group__g2"}
    assert asset_graph.get(AssetKey("c")).tags == {"tag": "val", "group_name_tag": "group__g2"}


def test_render_attributes_custom_context() -> None:
    op = ReplaceAttributes(
        operation="replace", target="group:g2", tags={"a": "{{ foo }}", "b": "prefix_{{ foo }}"}
    )

    newdefs = op.apply(defs, TemplatedValueResolver.default().with_context(foo="theval"))
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"a": "theval", "b": "prefix_theval"}
    assert asset_graph.get(AssetKey("c")).tags == {"a": "theval", "b": "prefix_theval"}


@pytest.mark.parametrize(
    "python,expected",
    [
        # default to merge and a * target
        ({"tags": {"a": "b"}}, MergeAttributes(target="*", tags={"a": "b"})),
        (
            {"operation": "replace", "tags": {"a": "b"}},
            ReplaceAttributes(operation="replace", target="*", tags={"a": "b"}),
        ),
        # explicit target
        (
            {"tags": {"a": "b"}, "target": "group:g2"},
            MergeAttributes(target="group:g2", tags={"a": "b"}),
        ),
        (
            {"operation": "replace", "tags": {"a": "b"}, "target": "group:g2"},
            ReplaceAttributes(operation="replace", target="group:g2", tags={"a": "b"}),
        ),
    ],
)
def test_load_attributes(python, expected) -> None:
    loaded = TypeAdapter(AssetAttributes).validate_python([python])
    assert len(loaded) == 1
    assert loaded[0] == expected
