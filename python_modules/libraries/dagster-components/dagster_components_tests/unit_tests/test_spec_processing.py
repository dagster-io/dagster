from collections.abc import Sequence

import pytest
from dagster import AssetKey, AssetSpec, AutomationCondition, Definitions
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    TemplatedValueResolver,
)
from pydantic import BaseModel, TypeAdapter


class M(BaseModel):
    asset_attributes: Sequence[AssetSpecTransformModel] = []


defs = Definitions(
    assets=[
        AssetSpec("a", group_name="g1"),
        AssetSpec("b", group_name="g2"),
        AssetSpec("c", group_name="g2", tags={"tag": "val"}),
    ],
)


def test_replace_attributes() -> None:
    op = AssetSpecTransformModel(
        operation="replace",
        target="group:g2",
        attributes=AssetAttributesModel(tags={"newtag": "newval"}),
    )

    newdefs = op.apply(defs, TemplatedValueResolver.default())
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"newtag": "newval"}


def test_merge_attributes() -> None:
    op = AssetSpecTransformModel(
        operation="merge",
        target="group:g2",
        attributes=AssetAttributesModel(tags={"newtag": "newval"}),
    )

    newdefs = op.apply(defs, TemplatedValueResolver.default())
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(AssetKey("c")).tags == {"tag": "val", "newtag": "newval"}


def test_render_attributes_asset_context() -> None:
    op = AssetSpecTransformModel(
        attributes=AssetAttributesModel(tags={"group_name_tag": "group__{{ asset.group_name }}"})
    )

    newdefs = op.apply(defs, TemplatedValueResolver.default().with_scope(foo="theval"))
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {"group_name_tag": "group__g1"}
    assert asset_graph.get(AssetKey("b")).tags == {"group_name_tag": "group__g2"}
    assert asset_graph.get(AssetKey("c")).tags == {"tag": "val", "group_name_tag": "group__g2"}


def test_render_attributes_custom_context() -> None:
    op = AssetSpecTransformModel(
        operation="replace",
        target="group:g2",
        attributes=AssetAttributesModel(
            tags={"a": "{{ foo }}", "b": "prefix_{{ foo }}"},
            metadata="{{ metadata }}",
            automation_condition="{{ custom_cron('@daily') }}",
        ),
    )

    def _custom_cron(s):
        return AutomationCondition.cron_tick_passed(s) & ~AutomationCondition.in_progress()

    metadata = {"a": 1, "b": "str", "d": 1.23}
    newdefs = op.apply(
        defs,
        TemplatedValueResolver.default().with_scope(
            foo="theval", metadata=metadata, custom_cron=_custom_cron
        ),
    )
    asset_graph = newdefs.get_asset_graph()
    assert asset_graph.get(AssetKey("a")).tags == {}
    assert asset_graph.get(AssetKey("a")).metadata == {}
    assert asset_graph.get(AssetKey("a")).automation_condition is None

    for k in ["b", "c"]:
        node = asset_graph.get(AssetKey(k))
        assert node.tags == {"a": "theval", "b": "prefix_theval"}
        assert node.metadata == metadata
        assert node.automation_condition == _custom_cron("@daily")


@pytest.mark.parametrize(
    "python,expected",
    [
        # default to merge and a * target
        (
            {"attributes": {"tags": {"a": "b"}}},
            AssetSpecTransformModel(target="*", attributes=AssetAttributesModel(tags={"a": "b"})),
        ),
        (
            {"operation": "replace", "attributes": {"tags": {"a": "b"}}},
            AssetSpecTransformModel(
                operation="replace",
                target="*",
                attributes=AssetAttributesModel(tags={"a": "b"}),
            ),
        ),
        # explicit target
        (
            {"attributes": {"tags": {"a": "b"}}, "target": "group:g2"},
            AssetSpecTransformModel(
                target="group:g2",
                attributes=AssetAttributesModel(tags={"a": "b"}),
            ),
        ),
        (
            {"operation": "replace", "attributes": {"tags": {"a": "b"}}, "target": "group:g2"},
            AssetSpecTransformModel(
                operation="replace",
                target="group:g2",
                attributes=AssetAttributesModel(tags={"a": "b"}),
            ),
        ),
    ],
)
def test_load_attributes(python, expected) -> None:
    loaded = TypeAdapter(Sequence[AssetSpecTransformModel]).validate_python([python])
    assert len(loaded) == 1
    assert loaded[0] == expected
