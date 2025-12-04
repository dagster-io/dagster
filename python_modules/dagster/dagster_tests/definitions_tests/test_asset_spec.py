from collections.abc import Sequence
from typing import cast

import dagster as dg
import pytest
from dagster import AutoMaterializePolicy, AutomationCondition
from dagster._check import CheckError
from pydantic import BaseModel, TypeAdapter


def test_validate_asset_owner() -> None:
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Invalid owner"):
        dg.AssetSpec(key="asset1", owners=["owner@$#&*1"])


def test_validate_group_name() -> None:
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="is not a valid name"):
        dg.AssetSpec(key="asset1", group_name="group@$#&*1")

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Empty asset group name was provided, which is not permitted",
    ):
        dg.AssetSpec(key="asset1", group_name="")


def test_resolve_automation_condition() -> None:
    ac_spec = dg.AssetSpec(key="asset1", automation_condition=AutomationCondition.eager())
    assert isinstance(ac_spec.auto_materialize_policy, dg.AutoMaterializePolicy)
    assert isinstance(ac_spec.automation_condition, dg.AutomationCondition)

    amp_spec = dg.AssetSpec(key="asset1", auto_materialize_policy=AutoMaterializePolicy.eager())
    assert isinstance(amp_spec.auto_materialize_policy, dg.AutoMaterializePolicy)
    assert isinstance(amp_spec.automation_condition, dg.AutomationCondition)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="both `automation_condition` and `auto_materialize_policy`",
    ):
        dg.AssetSpec(
            key="asset1",
            automation_condition=AutomationCondition.eager(),
            auto_materialize_policy=AutoMaterializePolicy.eager(),
        )


def test_replace_attributes_basic() -> None:
    spec = dg.AssetSpec(key="foo")
    assert spec.key == dg.AssetKey("foo")

    new_spec = spec.replace_attributes(key="bar")
    assert new_spec.key == dg.AssetKey("bar")

    spec_with_metadata = dg.AssetSpec(key="foo", metadata={"foo": "bar"})
    assert spec_with_metadata.metadata == {"foo": "bar"}

    spec_with_replace_metadata = spec_with_metadata.replace_attributes(metadata={"bar": "baz"})
    assert spec_with_replace_metadata.metadata == {"bar": "baz"}


def test_replace_attributes_kinds() -> None:
    spec = dg.AssetSpec(key="foo", kinds={"foo"}, tags={"a": "b"})
    assert spec.kinds == {"foo"}
    assert spec.tags == {"a": "b", "dagster/kind/foo": ""}

    new_spec = spec.replace_attributes(kinds={"bar"}, tags={"c": "d"})
    assert new_spec.kinds == {"bar"}
    assert new_spec.tags == {"c": "d", "dagster/kind/bar": ""}

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        kinds = {f"kind_{i}" for i in range(11)}
        spec.replace_attributes(kinds=kinds)


def test_replace_attributes_deps_coercion() -> None:
    spec = dg.AssetSpec(key="foo", deps={dg.AssetKey("bar")})
    assert spec.deps == [dg.AssetDep(dg.AssetKey("bar"))]

    new_spec = spec.replace_attributes(deps={dg.AssetKey("baz")})
    assert new_spec.deps == [dg.AssetDep(dg.AssetKey("baz"))]


def test_replace_attributes_group() -> None:
    spec = dg.AssetSpec(key="foo", group_name="group1")
    assert spec.group_name == "group1"

    new_spec = spec.replace_attributes(group_name="group2")
    assert new_spec.group_name == "group2"

    new_spec_no_group = spec.replace_attributes(group_name=None)
    assert new_spec_no_group.group_name is None


def test_merge_attributes_metadata() -> None:
    spec = dg.AssetSpec(key="foo")
    assert spec.key == dg.AssetKey("foo")

    new_spec = spec.merge_attributes(metadata={"bar": "baz"})
    assert new_spec.key == dg.AssetKey("foo")
    assert new_spec.metadata == {"bar": "baz"}

    spec_new_meta_key = new_spec.merge_attributes(metadata={"baz": "qux"})
    assert spec_new_meta_key.metadata == {"bar": "baz", "baz": "qux"}

    spec_replace_meta = spec_new_meta_key.merge_attributes(metadata={"bar": "qux"})
    assert spec_replace_meta.metadata == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_tags() -> None:
    spec = dg.AssetSpec(key="foo")
    assert spec.key == dg.AssetKey("foo")

    new_spec = spec.merge_attributes(tags={"bar": "baz"})
    assert new_spec.key == dg.AssetKey("foo")
    assert new_spec.tags == {"bar": "baz"}

    spec_new_tags_key = new_spec.merge_attributes(tags={"baz": "qux"})
    assert spec_new_tags_key.tags == {"bar": "baz", "baz": "qux"}

    spec_replace_tags = spec_new_tags_key.merge_attributes(tags={"bar": "qux"})
    assert spec_replace_tags.tags == {"bar": "qux", "baz": "qux"}


def test_merge_attributes_owners() -> None:
    spec = dg.AssetSpec(key="foo")
    assert spec.key == dg.AssetKey("foo")

    new_spec = spec.merge_attributes(owners=["owner1@dagsterlabs.com"])
    assert new_spec.key == dg.AssetKey("foo")
    assert new_spec.owners == ["owner1@dagsterlabs.com"]

    spec_new_owner = new_spec.merge_attributes(owners=["owner2@dagsterlabs.com"])
    assert spec_new_owner.owners == ["owner1@dagsterlabs.com", "owner2@dagsterlabs.com"]

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        spec_new_owner.merge_attributes(owners=["notvalid"])


def test_merge_attributes_deps() -> None:
    spec = dg.AssetSpec(key="foo")
    assert spec.key == dg.AssetKey("foo")

    new_spec = spec.merge_attributes(deps={dg.AssetKey("bar")})
    assert new_spec.key == dg.AssetKey("foo")
    assert new_spec.deps == [dg.AssetDep(dg.AssetKey("bar"))]

    spec_new_dep = new_spec.merge_attributes(deps={dg.AssetKey("baz")})
    assert spec_new_dep.deps == [dg.AssetDep(dg.AssetKey("bar")), dg.AssetDep(dg.AssetKey("baz"))]


def test_map_asset_specs_basic_specs() -> None:
    specs = [
        dg.AssetSpec(key="foo"),
        dg.AssetSpec(key="bar"),
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
        dg.AssetSpec(key="bar"),
    ]

    mapped_specs_and_defs = dg.map_asset_specs(
        lambda spec: spec.replace_attributes(owners=["ben@dagsterlabs.com"]), spec_and_defs
    )

    assert all(
        spec.owners == ["ben@dagsterlabs.com"]
        for spec in cast("dg.AssetsDefinition", mapped_specs_and_defs[0]).specs
    )
    assert cast("dg.AssetSpec", mapped_specs_and_defs[1]).owners == ["ben@dagsterlabs.com"]


def test_map_asset_specs_multi_asset() -> None:
    @dg.multi_asset(
        specs=[
            dg.AssetSpec(key="foo"),
            dg.AssetSpec(key="bar"),
        ]
    )
    def my_multi_asset():
        pass

    @dg.multi_asset(
        specs=[
            dg.AssetSpec(key="baz"),
            dg.AssetSpec(key="qux"),
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


def test_map_asset_specs_additional_deps() -> None:
    @dg.multi_asset(specs=[dg.AssetSpec(key="a")])
    def my_asset():
        pass

    @dg.multi_asset(specs=[dg.AssetSpec(key="c", deps=["a"])])
    def my_other_asset():
        pass

    assets = [my_asset, my_other_asset]

    mapped_assets = dg.map_asset_specs(
        lambda spec: spec.merge_attributes(deps=["b"]) if spec.key == my_other_asset.key else spec,
        assets,
    )

    c_asset = next(iter(asset for asset in mapped_assets if asset.key == my_other_asset.key))
    assert set(next(iter(c_asset.specs)).deps) == {dg.AssetDep("a"), dg.AssetDep("b")}


def test_map_asset_specs_multiple_deps_same_key() -> None:
    @dg.multi_asset(specs=[dg.AssetSpec(key="a", deps=[dg.AssetDep("b")])])
    def my_asset():
        pass

    # This works because the dep is coerced to an identical object.

    dg.map_asset_specs(lambda spec: spec.merge_attributes(deps=[dg.AssetKey("b")]), [my_asset])

    # This doesn't work because we change the object.
    with pytest.raises(dg.DagsterInvariantViolationError):
        dg.map_asset_specs(
            lambda spec: spec.merge_attributes(
                deps=[dg.AssetDep(dg.AssetKey("b"), partition_mapping=dg.LastPartitionMapping())]
            ),
            [my_asset],
        )


def test_map_asset_specs_nonarg_dep_removal() -> None:
    @dg.multi_asset(specs=[dg.AssetSpec(key="a", deps=[dg.AssetDep("b")])])
    def my_asset():
        pass

    new_asset = next(
        iter(dg.map_asset_specs(lambda spec: spec.replace_attributes(deps=[]), [my_asset]))
    )
    new_spec = next(iter(new_asset.specs))
    assert new_spec.deps == []
    # Ensure that dep removal propogated to the underlying op
    assert new_asset.keys_by_input_name == {}
    assert len(new_asset.op.input_defs) == 0


def test_map_asset_specs_arg_dep_removal() -> None:
    @dg.asset(key="a")
    def my_asset(b):
        pass

    with pytest.raises(CheckError):
        dg.map_asset_specs(lambda spec: spec.replace_attributes(deps=[]), [my_asset])


def test_map_additional_deps_partition_mapping() -> None:
    @dg.multi_asset(
        specs=[
            dg.AssetSpec(
                key="a", deps=[dg.AssetDep("b", partition_mapping=dg.LastPartitionMapping())]
            )
        ]
    )
    def my_asset():
        pass

    a_asset = next(
        iter(
            dg.map_asset_specs(
                lambda spec: spec.merge_attributes(
                    deps=[dg.AssetDep("c", partition_mapping=dg.IdentityPartitionMapping())]
                ),
                [my_asset],
            )
        )
    )
    a_spec = next(iter(a_asset.specs))
    b_dep = next(iter(dep for dep in a_spec.deps if dep.asset_key == dg.AssetKey("b")))
    assert b_dep.partition_mapping == dg.LastPartitionMapping()
    c_dep = next(iter(dep for dep in a_spec.deps if dep.asset_key == dg.AssetKey("c")))
    assert c_dep.partition_mapping == dg.IdentityPartitionMapping()
    assert a_asset.get_partition_mapping(dg.AssetKey("c")) == dg.IdentityPartitionMapping()
    assert a_asset.get_partition_mapping(dg.AssetKey("b")) == dg.LastPartitionMapping()


def test_add_specs_non_executable_asset() -> None:
    assets_def = (
        dg.Definitions(assets=[dg.AssetSpec(key="foo")])
        .get_repository_def()
        .assets_defs_by_key[dg.AssetKey("foo")]
    )
    foo_spec = next(
        iter(
            next(
                iter(
                    dg.map_asset_specs(lambda spec: spec.merge_attributes(deps=["a"]), [assets_def])
                )
            ).specs
        )
    )
    assert foo_spec.deps == [dg.AssetDep("a")]


def test_graph_backed_asset_additional_deps() -> None:
    @dg.op
    def foo_op():
        pass

    @dg.graph_asset()
    def foo():
        return foo_op()

    with pytest.raises(CheckError):
        dg.map_asset_specs(lambda spec: spec.merge_attributes(deps=["baz"]), [foo])


def test_static_partition_mapping_dep() -> None:
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["1", "2"]))
    def b():
        pass

    @dg.multi_asset(
        specs=[
            dg.AssetSpec(
                key="a",
                partitions_def=dg.StaticPartitionsDefinition(["1", "2"]),
                deps=[
                    dg.AssetDep(
                        "b", partition_mapping=dg.StaticPartitionMapping({"1": "1", "2": "2"})
                    )
                ],
            )
        ]
    )
    def my_asset():
        pass

    a_asset = next(
        iter(
            dg.map_asset_specs(
                lambda spec: spec.merge_attributes(
                    deps=[
                        dg.AssetDep(
                            "c", partition_mapping=dg.StaticPartitionMapping({"1": "1", "2": "2"})
                        )
                    ]
                ),
                [my_asset],
            )
        )
    )

    a_spec = next(iter(a_asset.specs))
    b_dep = next(iter(dep for dep in a_spec.deps if dep.asset_key == dg.AssetKey("b")))
    c_dep = next(iter(dep for dep in a_spec.deps if dep.asset_key == dg.AssetKey("c")))
    assert b_dep.partition_mapping == dg.StaticPartitionMapping({"1": "1", "2": "2"})
    assert c_dep.partition_mapping == dg.StaticPartitionMapping({"1": "1", "2": "2"})


def test_pydantic_spec() -> None:
    class SpecHolder(BaseModel):
        spec: dg.AssetSpec
        spec_list: Sequence[dg.AssetSpec]

    holder = SpecHolder(spec=dg.AssetSpec(key="foo"), spec_list=[dg.AssetSpec(key="bar")])
    assert TypeAdapter(SpecHolder).validate_python(holder)


def test_definitions_spec_collision():
    first = dg.AssetSpec("a", group_name="first")
    second = dg.AssetSpec("a", group_name="second")

    dg.AssetsDefinition(specs=[first, first])
    assert dg.Definitions(assets=[first, first]).resolve_all_asset_specs() == [first]

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="conflicting AssetSpec"):
        dg.AssetsDefinition(specs=[first, second])

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="conflicting AssetSpec"):
        dg.Definitions(assets=[first, second]).resolve_all_asset_specs()
