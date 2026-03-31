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


def test_source_asset_with_wildcard_post_processing() -> None:
    """SourceAssets in Definitions should not cause errors during post-processing."""

    @dg.asset
    def my_asset() -> None:
        pass

    source = dg.SourceAsset(key="my_source")
    mixed_defs = dg.Definitions(assets=[my_asset, source])

    op = AssetPostProcessorModel.model()(
        target="*",
        attributes={"tags": {"processed": "true"}},
    )

    # This should NOT raise DagsterInvariantViolationError
    newdefs = apply_post_processor_to_defs(
        model=op, defs=mixed_defs, context=ResolutionContext.default()
    )

    # Verify the @asset got post-processed
    found_regular = False
    found_source = False
    for asset_def in newdefs.assets or []:
        if isinstance(asset_def, dg.AssetsDefinition):
            for spec in asset_def.specs:
                if spec.key == dg.AssetKey("my_asset"):
                    assert spec.tags.get("processed") == "true"
                    found_regular = True
        elif isinstance(asset_def, dg.SourceAsset):
            assert asset_def.key == dg.AssetKey("my_source")
            found_source = True

    assert found_regular, "regular asset should be post-processed"
    assert found_source, "SourceAsset should be preserved"


def test_source_asset_with_targeted_post_processing() -> None:
    """SourceAssets should be preserved when post-processing targets specific assets."""

    @dg.asset(group_name="target_group")
    def targeted_asset() -> None:
        pass

    @dg.asset(group_name="other_group")
    def other_asset() -> None:
        pass

    source = dg.SourceAsset(key="my_source")
    mixed_defs = dg.Definitions(assets=[targeted_asset, other_asset, source])

    op = AssetPostProcessorModel.model()(
        target="group:target_group",
        attributes={"tags": {"processed": "true"}},
    )

    newdefs = apply_post_processor_to_defs(
        model=op, defs=mixed_defs, context=ResolutionContext.default()
    )

    found_targeted = False
    found_other = False
    found_source = False
    for asset_def in newdefs.assets or []:
        if isinstance(asset_def, dg.AssetsDefinition):
            for spec in asset_def.specs:
                if spec.key == dg.AssetKey("targeted_asset"):
                    assert spec.tags.get("processed") == "true"
                    found_targeted = True
                elif spec.key == dg.AssetKey("other_asset"):
                    assert spec.tags.get("processed") is None
                    found_other = True
        elif isinstance(asset_def, dg.SourceAsset):
            found_source = True

    assert found_targeted, "targeted asset should be post-processed"
    assert found_other, "non-targeted asset should be unchanged"
    assert found_source, "SourceAsset should be preserved"


def test_cacheable_assets_with_post_processing() -> None:
    """CacheableAssetsDefinitions should not cause errors during post-processing."""
    from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
        AssetsDefinitionCacheableData,
        CacheableAssetsDefinition,
    )

    class MyCacheableAssets(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_output_name={"result": dg.AssetKey("cacheable_asset")},
                )
            ]

        def build_definitions(self, data):
            @dg.op(name="cacheable_op")
            def _op():
                return 1

            return [
                dg.AssetsDefinition.from_op(
                    _op,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    @dg.asset
    def regular_asset() -> None:
        pass

    mixed_defs = dg.Definitions(assets=[regular_asset, MyCacheableAssets("test")])

    op = AssetPostProcessorModel.model()(
        target="*",
        attributes={"tags": {"processed": "true"}},
    )

    # This should NOT raise DagsterInvariantViolationError
    newdefs = apply_post_processor_to_defs(
        model=op, defs=mixed_defs, context=ResolutionContext.default()
    )

    found_regular = False
    found_cacheable = False
    for asset_def in newdefs.assets or []:
        if isinstance(asset_def, dg.AssetsDefinition):
            for spec in asset_def.specs:
                if spec.key == dg.AssetKey("regular_asset"):
                    assert spec.tags.get("processed") == "true"
                    found_regular = True
        elif isinstance(asset_def, CacheableAssetsDefinition):
            found_cacheable = True

    assert found_regular, "regular asset should be post-processed"
    assert found_cacheable, "CacheableAssetsDefinition should be preserved"
