from collections.abc import Iterator
from typing import Annotated

import dagster as dg
import pytest
from dagster._core.definitions.assets.definition.asset_effect import (
    AssetCheckEffect,
    AssetMaterializationEffect,
    Effect,
)
from dagster._core.definitions.assets.definition.computation import Computation
from dagster.components.resolved.core_models import OpSpec


class MyConfig(dg.Config):
    a: int
    b: str


class MyResource(dg.ConfigurableResource):
    c: float
    d: bool


def test_computation_from_fn_no_params() -> None:
    def _fn(): ...  # -> Iterator[dg.MaterializeResult]: ...

    specs = [
        dg.AssetSpec(key=dg.AssetKey(["prefix", "a"])),
        dg.AssetCheckSpec(name="asset_check1", asset=dg.AssetKey(["prefix", "a"])),
    ]
    computation = Computation.from_fn(
        fn=_fn,  # type: ignore
        op_spec=OpSpec(name="test_op"),
        effects=[Effect.from_coercible(spec) for spec in specs],
        can_subset=False,
    )

    assert computation.node_def.name == "test_op"

    # Test Outputs
    output_defs = computation.node_def.output_dict
    assert len(output_defs) == 2

    asset_output = output_defs["prefix__a"]
    assert asset_output.name == "prefix__a"
    assert asset_output.dagster_type.is_any
    assert asset_output.description is None
    assert asset_output.is_required

    asset_check_output = output_defs["prefix__a_asset_check1"]
    assert asset_check_output.name == "prefix__a_asset_check1"
    assert asset_check_output.dagster_type.is_nothing
    assert asset_check_output.description is None
    assert asset_check_output.is_required

    assert len(computation.output_mappings) == 2
    assert computation.output_mappings["prefix__a"] == AssetMaterializationEffect(
        spec=dg.AssetSpec(key=dg.AssetKey(["prefix", "a"]))
    )
    assert computation.output_mappings["prefix__a_asset_check1"] == AssetCheckEffect(
        spec=dg.AssetCheckSpec(name="asset_check1", asset=dg.AssetKey(["prefix", "a"]))
    )

    # Test Inputs
    input_defs = computation.node_def.input_defs
    assert len(input_defs) == 0


def test_computation_from_fn_with_complex_deps_and_additional_args() -> None:
    def _fn(
        context: dg.AssetExecutionContext,
        config: MyConfig,
        my_res: MyResource,
        # asset inputs
        a: int,
        b: str,
    ):  # -> Iterator[Union[dg.MaterializeResult, dg.AssetCheckResult]]:
        yield dg.MaterializeResult(asset_key="asset1", value=1)
        yield dg.MaterializeResult(asset_key="asset2")
        yield dg.MaterializeResult(asset_key="asset3", value=3)
        yield dg.AssetCheckResult(asset_key="asset1", passed=True)
        yield dg.AssetCheckResult(asset_key="asset2", passed=True)

    specs = [
        dg.AssetSpec(key="asset1", deps=["a"]).with_dagster_type(int),
        dg.AssetSpec(key="asset2", deps=["a", "b"]),
        dg.AssetSpec(key="asset3", deps=["asset1", "asset2", "b", "d"]),
        dg.AssetCheckSpec(name="asset_check1", asset="asset1", additional_deps=["a", "c"]),
        dg.AssetCheckSpec(name="asset_check2", asset="asset2"),
    ]
    computation = Computation.from_fn(
        fn=_fn,
        op_spec=OpSpec(name="test_op"),
        effects=[Effect.from_coercible(spec) for spec in specs],
        can_subset=False,
    )

    assert computation.node_def.name == "test_op"

    # Test Outputs
    output_defs = computation.node_def.output_dict
    assert len(output_defs) == 5

    asset1_output = output_defs["asset1"]
    assert asset1_output.name == "asset1"
    assert asset1_output.dagster_type.display_name == "Int"

    asset2_output = output_defs["asset2"]
    assert asset2_output.name == "asset2"
    assert asset2_output.dagster_type.is_any

    asset3_output = output_defs["asset3"]
    assert asset3_output.name == "asset3"
    assert asset3_output.dagster_type.is_any

    asset_check1_output = output_defs["asset1_asset_check1"]
    assert asset_check1_output.name == "asset1_asset_check1"
    assert asset_check1_output.dagster_type.is_nothing

    asset_check2_output = output_defs["asset2_asset_check2"]
    assert asset_check2_output.name == "asset2_asset_check2"
    assert asset_check2_output.dagster_type.is_nothing

    # Test Inputs
    input_defs = computation.node_def.input_dict
    assert len(input_defs) == 4

    a_input = input_defs["a"]
    assert a_input.dagster_type.display_name == "Int"

    b_input = input_defs["b"]
    assert b_input.dagster_type.display_name == "String"

    c_input = input_defs["c"]
    assert c_input.dagster_type.is_nothing

    d_input = input_defs["d"]
    assert d_input.dagster_type.is_nothing

    # Test Execution
    @dg.asset
    def a() -> int:
        return 1

    @dg.asset
    def b() -> str:
        return "b"

    assets_def = computation.to_assets_def()
    result = dg.materialize_to_memory(
        [a, b, assets_def],
        resources={"my_res": MyResource(c=1, d=True)},
        run_config=dg.RunConfig(ops={"test_op": {"config": {"a": 1, "b": "b"}}}),
    )
    assert result.success


@pytest.mark.skip
def test_computation_from_fn_with_complex_deps_and_asset_ins() -> None:
    # currently not supported
    def _fn(
        config: MyConfig,
        my_res: MyResource,
        a: int,
        b_renamed: Annotated[str, dg.AssetIn(key=dg.AssetKey("b"))],
    ) -> Iterator[dg.MaterializeResult]: ...


def test_computation_from_fn_spec_properties() -> None:
    def _fn(): ...  # -> Iterator[dg.MaterializeResult]: ...

    metadata = {"foo": 1, "bar": "baz"}
    tags = {"test_tag": "test_value"}
    specs = [
        dg.AssetSpec(key="asset1", metadata=metadata, code_version="1a"),
        dg.AssetCheckSpec(name="asset_check1", metadata=metadata, asset="asset1"),
    ]
    effects = [Effect.from_coercible(spec) for spec in specs]
    computation = Computation.from_fn(
        fn=_fn,  # type: ignore
        op_spec=OpSpec(
            name="test_op",
            description="test_description",
            tags=tags,
            pool="test_pool",
        ),
        effects=effects,
        can_subset=False,
    )

    # Test Node Properties
    assert computation.node_def.name == "test_op"
    assert computation.node_def.description == "test_description"
    assert computation.node_def.tags == {"test_tag": "test_value"}
    assert computation.node_def.pools == {"test_pool"}

    # Test Outputs
    output_defs = computation.node_def.output_dict
    assert len(output_defs) == 2

    asset_output = output_defs["asset1"]
    assert asset_output.name == "asset1"
    assert asset_output.description is None
    assert asset_output.code_version == "1a"
    assert asset_output.metadata == metadata

    asset_check_output = output_defs["asset1_asset_check1"]
    assert asset_check_output.name == "asset1_asset_check1"
    assert asset_check_output.description is None
    assert asset_check_output.metadata == metadata
