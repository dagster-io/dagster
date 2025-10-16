from collections.abc import Sequence

import dagster as dg
import pytest
from dagster import AutomationCondition
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import (
    AssetPostProcessorModel,
    apply_post_processor_to_defs,
)
from dagster.components.utils import TranslatorResolvingInfo
from pydantic import BaseModel, TypeAdapter


class M(BaseModel):
    asset_attributes: Sequence[AssetPostProcessorModel] = []


defs = dg.Definitions(
    assets=[
        dg.AssetSpec("a", group_name="g1"),
        dg.AssetSpec("b", group_name="g2"),
        dg.AssetSpec("c", group_name="g2", tags={"tag": "val"}),
    ],
)


def test_replace_attributes() -> None:
    op = AssetPostProcessorModel.model()(
        operation="replace",
        target="group:g2",
        attributes={"tags": {"newtag": "newval"}},
    )

    newdefs = apply_post_processor_to_defs(model=op, defs=defs, context=ResolutionContext.default())
    asset_graph = newdefs.resolve_asset_graph()
    assert asset_graph.get(dg.AssetKey("a")).tags == {}
    assert asset_graph.get(dg.AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(dg.AssetKey("c")).tags == {"newtag": "newval"}


def test_merge_attributes() -> None:
    op = AssetPostProcessorModel.model()(
        operation="merge",
        target="group:g2",
        attributes={"tags": {"newtag": "newval"}},
    )

    newdefs = apply_post_processor_to_defs(model=op, defs=defs, context=ResolutionContext.default())
    asset_graph = newdefs.resolve_asset_graph()
    assert asset_graph.get(dg.AssetKey("a")).tags == {}
    assert asset_graph.get(dg.AssetKey("b")).tags == {"newtag": "newval"}
    assert asset_graph.get(dg.AssetKey("c")).tags == {"tag": "val", "newtag": "newval"}


def test_render_attributes_asset_context() -> None:
    op = AssetPostProcessorModel.model()(
        attributes={"tags": {"group_name_tag": "group__{{ asset.group_name }}"}}
    )

    newdefs = apply_post_processor_to_defs(model=op, defs=defs, context=ResolutionContext.default())
    asset_graph = newdefs.resolve_asset_graph()
    assert asset_graph.get(dg.AssetKey("a")).tags == {"group_name_tag": "group__g1"}
    assert asset_graph.get(dg.AssetKey("b")).tags == {"group_name_tag": "group__g2"}
    assert asset_graph.get(dg.AssetKey("c")).tags == {"tag": "val", "group_name_tag": "group__g2"}


def test_render_attributes_custom_context() -> None:
    op = AssetPostProcessorModel.model()(
        operation="replace",
        target="group:g2",
        attributes={
            "tags": {"a": "{{ foo }}", "b": "prefix_{{ foo }}"},
            "metadata": "{{ metadata }}",
            "automation_condition": "{{ custom_cron('@daily') }}",
        },
    )

    def _custom_cron(s):
        return AutomationCondition.cron_tick_passed(s) & ~AutomationCondition.in_progress()

    metadata = {"a": 1, "b": "str", "d": 1.23}
    newdefs = apply_post_processor_to_defs(
        model=op,
        defs=defs,
        context=ResolutionContext.default().with_scope(
            foo="theval", metadata=metadata, custom_cron=_custom_cron
        ),
    )
    asset_graph = newdefs.resolve_asset_graph()
    assert asset_graph.get(dg.AssetKey("a")).tags == {}
    assert asset_graph.get(dg.AssetKey("a")).metadata == {}
    assert asset_graph.get(dg.AssetKey("a")).automation_condition is None

    for k in ["b", "c"]:
        node = asset_graph.get(dg.AssetKey(k))
        assert node.tags == {"a": "theval", "b": "prefix_theval"}
        assert node.metadata == metadata
        assert node.automation_condition == _custom_cron("@daily")


@pytest.mark.parametrize(
    "python,expected",
    [
        # default to merge and a * target
        (
            {"attributes": {"tags": {"a": "b"}}},
            AssetPostProcessorModel.model()(target="*", attributes={"tags": {"a": "b"}}),
        ),
        (
            {"operation": "replace", "attributes": {"tags": {"a": "b"}}},
            AssetPostProcessorModel.model()(
                operation="replace",
                target="*",
                attributes={"tags": {"a": "b"}},
            ),
        ),
        # explicit target
        (
            {"attributes": {"tags": {"a": "b"}}, "target": "group:g2"},
            AssetPostProcessorModel.model()(
                target="group:g2",
                attributes={"tags": {"a": "b"}},
            ),
        ),
        (
            {"operation": "replace", "attributes": {"tags": {"a": "b"}}, "target": "group:g2"},
            AssetPostProcessorModel.model()(
                operation="replace",
                target="group:g2",
                attributes={"tags": {"a": "b"}},
            ),
        ),
    ],
)
def test_load_attributes(python, expected) -> None:
    loaded = TypeAdapter(Sequence[AssetPostProcessorModel.model()]).validate_python([python])
    assert len(loaded) == 1
    assert loaded[0] == expected


def test_prefixing():
    prefix = ["sweet_prefix"]
    translated = TranslatorResolvingInfo(
        resolution_context=ResolutionContext.default(),
        asset_attributes=dg.AssetAttributesModel(
            key_prefix=prefix,
        ),
    ).get_asset_spec(dg.AssetSpec("a"), {})

    assert translated.key.has_prefix(prefix)


def test_key_set():
    spec = dg.AssetSpec("a")
    translated = TranslatorResolvingInfo(
        resolution_context=ResolutionContext.default(),
        asset_attributes=dg.AssetAttributesModel(
            key="{{ spec.key.to_user_string() + '_key' }}",
        ),
    ).get_asset_spec(spec, {"spec": spec})

    assert translated.key.to_user_string().endswith("_key")


def test_key_and_prefix():
    prefix = ["sweet_prefix"]
    spec = dg.AssetSpec("a")
    translated = TranslatorResolvingInfo(
        resolution_context=ResolutionContext.default(),
        asset_attributes=dg.AssetAttributesModel(
            key="{{ spec.key.to_user_string() + '_key' }}",
            key_prefix=prefix,
        ),
    ).get_asset_spec(spec, {"spec": spec})

    assert translated.key.to_user_string().endswith("_key")
    assert translated.key.has_prefix(prefix)
