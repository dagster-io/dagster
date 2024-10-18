import pytest
from dagster import AssetSpec, AutoMaterializePolicy, AutomationCondition
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import merge_attributes, replace_attributes
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

    new_spec = replace_attributes(spec, key="bar")
    assert new_spec.key == AssetKey("bar")

    spec_with_metadata = AssetSpec(key="foo", metadata={"foo": "bar"})
    assert spec_with_metadata.metadata == {"foo": "bar"}

    spec_with_replace_metadata = replace_attributes(spec_with_metadata, metadata={"bar": "baz"})
    assert spec_with_replace_metadata.metadata == {"bar": "baz"}


def test_replace_attributes_kinds() -> None:
    spec = AssetSpec(key="foo", kinds={"foo"}, tags={"a": "b"})
    assert spec.kinds == {"foo"}
    assert spec.tags == {"a": "b", "dagster/kind/foo": ""}

    new_spec = replace_attributes(spec, kinds={"bar"}, tags={"c": "d"})
    assert new_spec.kinds == {"bar"}
    assert new_spec.tags == {"c": "d", "dagster/kind/bar": ""}

    with pytest.raises(DagsterInvalidDefinitionError):
        replace_attributes(spec, kinds={"a", "b", "c", "d", "e"})


def test_replace_attributes_deps_coercion() -> None:
    spec = AssetSpec(key="foo", deps={AssetKey("bar")})
    assert spec.deps == [AssetDep(AssetKey("bar"))]

    new_spec = replace_attributes(spec, deps={AssetKey("baz")})
    assert new_spec.deps == [AssetDep(AssetKey("baz"))]


def test_replace_attributes_group() -> None:
    spec = AssetSpec(key="foo", group_name="group1")
    assert spec.group_name == "group1"

    new_spec = replace_attributes(spec, group_name="group2")
    assert new_spec.group_name == "group2"

    new_spec_no_group = replace_attributes(spec, group_name=None)
    assert new_spec_no_group.group_name is None


def test_merge_attributes_metadata() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = merge_attributes(spec, metadata={"bar": "baz"})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.metadata == {"bar": "baz"}

    spec_new_meta_key = merge_attributes(new_spec, metadata={"baz": "qux"})
    assert spec_new_meta_key.metadata == {"bar": "baz", "baz": "qux"}

    spec_replace_meta = merge_attributes(spec_new_meta_key, metadata={"bar": "qux"})
    assert spec_replace_meta.metadata == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_tags() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = merge_attributes(spec, tags={"bar": "baz"})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.tags == {"bar": "baz"}

    spec_new_tags_key = merge_attributes(new_spec, tags={"baz": "qux"})
    assert spec_new_tags_key.tags == {"bar": "baz", "baz": "qux"}

    spec_replace_tags = merge_attributes(spec_new_tags_key, tags={"bar": "qux"})
    assert spec_replace_tags.tags == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_owners() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = merge_attributes(spec, owners=["owner1@dagsterlabs.com"])
    assert new_spec.key == AssetKey("foo")
    assert new_spec.owners == ["owner1@dagsterlabs.com"]

    spec_new_owner = merge_attributes(new_spec, owners=["owner2@dagsterlabs.com"])
    assert spec_new_owner.owners == ["owner1@dagsterlabs.com", "owner2@dagsterlabs.com"]

    with pytest.raises(DagsterInvalidDefinitionError):
        merge_attributes(spec_new_owner, owners=["notvalid"])


def test_merge_attributes_deps() -> None:
    spec = AssetSpec(key="foo")
    assert spec.key == AssetKey("foo")

    new_spec = merge_attributes(spec, deps={AssetKey("bar")})
    assert new_spec.key == AssetKey("foo")
    assert new_spec.deps == [AssetDep(AssetKey("bar"))]

    spec_new_dep = merge_attributes(new_spec, deps={AssetKey("baz")})
    assert spec_new_dep.deps == [AssetDep(AssetKey("bar")), AssetDep(AssetKey("baz"))]
