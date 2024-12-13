import pytest
from dagster import AssetKey, AssetSpec, Definitions
from dagster_components.core.dsl_schema import AssetAttributes, MergeAttributes, ReplaceAttributes
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

    newdefs = op.apply(defs)
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"newtag": "newval"}


def test_merge_attributes() -> None:
    op = MergeAttributes(operation="merge", target="group:g2", tags={"newtag": "newval"})

    newdefs = op.apply(defs)
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"tag": "val", "newtag": "newval"}


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
