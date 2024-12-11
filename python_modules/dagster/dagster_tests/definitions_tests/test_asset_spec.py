from typing import cast

import dagster as dg
import pytest
from dagster import AssetSpec, AutoMaterializePolicy, AutomationCondition
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError


def test_validate_asset_owner() -> None:
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid owner"):
        AssetSpec(key="asset1", owners=["owner@$#&*1"])


def test_validate_group_name() -> None:
    with pytest.raises(DagsterInvalidDefinitionError, match="is not a valid name"):
        AssetSpec(key="asset1", group_name="group@$#&*1")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Empty asset group name was provided, which is not permitted",
    ):
        AssetSpec(key="asset1", group_name="")


def test_resolve_automation_condition() -> None:
    ac_spec = AssetSpec(key="asset1", automation_condition=AutomationCondition.eager())
    assert isinstance(ac_spec.auto_materialize_policy, AutoMaterializePolicy)
    assert isinstance(ac_spec.automation_condition, AutomationCondition)

    amp_spec = AssetSpec(key="asset1", auto_materialize_policy=AutoMaterializePolicy.eager())
    assert isinstance(amp_spec.auto_materialize_policy, AutoMaterializePolicy)
    assert isinstance(amp_spec.automation_condition, AutomationCondition)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="both `automation_condition` and `auto_materialize_policy`",
    ):
        AssetSpec(
            key="asset1",
            automation_condition=AutomationCondition.eager(),
            auto_materialize_policy=AutoMaterializePolicy.eager(),
        )


def test_replace_attributes_basic() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = spec.replace_attributes(key="bar")
    assert new_spec.key == AssetKey("bar")

    spec_with_metadata = AssetSpec(key="foo", metadata={"foo": "bar"})
    assert spec_with_metadata.metadata == {"foo": "bar"}

    spec_with_replace_metadata = spec_with_metadata.replace_attributes(metadata={"bar": "baz"})
    assert spec_with_replace_metadata.metadata == {"bar": "baz"}


def test_replace_attributes_kinds() -> None:
    spec = AssetSpec(key="foo", kinds={"foo"}, tags={"a": "b"})
    assert spec.kinds == {"foo"}
    assert spec.tags == {"a": "b", "dagster/kind/foo": ""}

    new_spec = spec.replace_attributes(kinds={"bar"}, tags={"c": "d"})
    assert new_spec.kinds == {"bar"}
    assert new_spec.tags == {"c": "d", "dagster/kind/bar": ""}

    with pytest.raises(DagsterInvalidDefinitionError):
        spec.replace_attributes(kinds={"a", "b", "c", "d", "e"})


def test_replace_attributes_deps_coercion() -> None:
    spec = AssetSpec(key="foo", deps={AssetKey("bar")})
    assert spec.deps == [AssetDep(AssetKey("bar"))]

    new_spec = spec.replace_attributes(deps={AssetKey("baz")})
    assert new_spec.deps == [AssetDep(AssetKey("baz"))]


def test_replace_attributes_group() -> None:
    spec = AssetSpec(key="foo", group_name="group1")
    assert spec.group_name == "group1"

    new_spec = spec.replace_attributes(group_name="group2")
    assert new_spec.group_name == "group2"

    new_spec_no_group = spec.replace_attributes(group_name=None)
    assert new_spec_no_group.group_name is None


def test_merge_attributes_metadata() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = spec.merge_attributes(metadata={"bar": "baz"})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.metadata == {"bar": "baz"}

    spec_new_meta_key = new_spec.merge_attributes(metadata={"baz": "qux"})
    assert spec_new_meta_key.metadata == {"bar": "baz", "baz": "qux"}

    spec_replace_meta = spec_new_meta_key.merge_attributes(metadata={"bar": "qux"})
    assert spec_replace_meta.metadata == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_tags() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = spec.merge_attributes(tags={"bar": "baz"})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.tags == {"bar": "baz"}

    spec_new_tags_key = new_spec.merge_attributes(tags={"baz": "qux"})
    assert spec_new_tags_key.tags == {"bar": "baz", "baz": "qux"}

    spec_replace_tags = spec_new_tags_key.merge_attributes(tags={"bar": "qux"})
    assert spec_replace_tags.tags == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_owners() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = spec.merge_attributes(owners=["owner1@dagsterlabs.com"])
    assert new_spec.key == AssetKey("foo")
    assert new_spec.owners == ["owner1@dagsterlabs.com"]

    spec_new_owner = new_spec.merge_attributes(owners=["owner2@dagsterlabs.com"])
    assert spec_new_owner.owners == ["owner1@dagsterlabs.com", "owner2@dagsterlabs.com"]

    with pytest.raises(DagsterInvalidDefinitionError):
        spec_new_owner.merge_attributes(owners=["notvalid"])


def test_merge_attributes_deps() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = spec.merge_attributes(deps={AssetKey("bar")})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.deps == [AssetDep(AssetKey("bar"))]

    spec_new_dep = new_spec.merge_attributes(deps={AssetKey("baz")})
    assert spec_new_dep.deps == [AssetDep(AssetKey("bar")), AssetDep(AssetKey("baz"))]


def test_map_asset_specs_basic_specs() -> None:
    specs = [
        AssetSpec(key="foo"),
        AssetSpec(key="bar"),
    ]

    mapped_specs = dg.map_asset_specs(
        lambda spec: spec.replace_attributes(owners=["ben@dagsterlabs.com"]), specs
    )

    assert all(spec.owners == ["ben@dagsterlabs.com"] for spec in mapped_specs)


def test_map_asset_specs_basic_defs() -> None:
    @dg.asset
    def my_asset():
        pass

    @dg.asset
    def my_other_asset():
        pass

    assets = [my_asset, my_other_asset]

    mapped_assets = dg.map_asset_specs(
        lambda spec: spec.replace_attributes(owners=["ben@dagsterlabs.com"]), assets
    )

    assert all(
        spec.owners == ["ben@dagsterlabs.com"] for asset in mapped_assets for spec in asset.specs
    )


def test_map_asset_specs_mixed_specs_defs() -> None:
    @dg.asset
    def my_asset():
        pass

    spec_and_defs = [
        my_asset,
        AssetSpec(key="bar"),
    ]

    mapped_specs_and_defs = dg.map_asset_specs(
        lambda spec: spec.replace_attributes(owners=["ben@dagsterlabs.com"]), spec_and_defs
    )

    assert all(
        spec.owners == ["ben@dagsterlabs.com"]
        for spec in cast(AssetsDefinition, mapped_specs_and_defs[0]).specs
    )
    assert cast(AssetSpec, mapped_specs_and_defs[1]).owners == ["ben@dagsterlabs.com"]


def test_map_asset_specs_multi_asset() -> None:
    @dg.multi_asset(
        specs=[
            AssetSpec(key="foo"),
            AssetSpec(key="bar"),
        ]
    )
    def my_multi_asset():
        pass

    @dg.multi_asset(
        specs=[
            AssetSpec(key="baz"),
            AssetSpec(key="qux"),
        ]
    )
    def my_other_multi_asset():
        pass

    assets = [my_multi_asset, my_other_multi_asset]

    mapped_assets = dg.map_asset_specs(
        lambda spec: spec.replace_attributes(owners=["ben@dagsterlabs.com"]), assets
    )

    assert all(
        spec.owners == ["ben@dagsterlabs.com"] for asset in mapped_assets for spec in asset.specs
    )
