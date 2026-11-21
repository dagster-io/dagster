from __future__ import annotations  # noqa: TID251

import dagster as dg
import pytest

# Types referenced by annotations must be defined at module scope, since postponed annotations are
# resolved against the module's globals.


class MyConfig(dg.Config):
    value: int


class MyResource(dg.ConfigurableResource):
    value: int


class RawResource:
    def __init__(self, value: int):
        self.value = value


def test_context_provided_to_asset():
    @dg.asset
    def no_annotation(context):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([no_annotation])

    @dg.asset
    def asset_annotation(context: dg.AssetExecutionContext):
        assert isinstance(context, dg.AssetExecutionContext)

    dg.materialize([asset_annotation])

    @dg.asset
    def op_annotation(context: dg.OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        # AssetExecutionContext is an instance of OpExecutionContext, so add this additional check
        assert not isinstance(context, dg.AssetExecutionContext)

    dg.materialize([op_annotation])


def test_context_provided_to_op():
    @dg.op
    def op_annotation(context: dg.OpExecutionContext):
        assert isinstance(context, dg.OpExecutionContext)
        assert not isinstance(context, dg.AssetExecutionContext)

    @dg.job
    def the_job():
        op_annotation()

    assert the_job.execute_in_process().success


def test_context_provided_to_graph_asset_op():
    @dg.op
    def asset_annotation(context: dg.AssetExecutionContext) -> int:
        assert isinstance(context, dg.AssetExecutionContext)
        return 1

    @dg.graph_asset
    def the_graph_asset():
        return asset_annotation()

    assert dg.materialize([the_graph_asset]).success


def test_context_provided_to_asset_check():
    @dg.asset
    def the_asset():
        pass

    @dg.asset_check(asset=the_asset)
    def check_annotation(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult:
        assert isinstance(context, dg.AssetCheckExecutionContext)
        return dg.AssetCheckResult(passed=True)

    assert dg.materialize([the_asset, check_annotation]).success


def test_error_on_invalid_context_annotation():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @dg.op
        def the_op(context: int):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank",
    ):

        @dg.asset
        def the_asset(context: int):
            pass


def test_config_annotation():
    @dg.asset
    def the_asset(context: dg.AssetExecutionContext, config: MyConfig) -> int:
        return config.value

    result = dg.materialize(
        [the_asset], run_config={"ops": {"the_asset": {"config": {"value": 5}}}}
    )
    assert result.output_for_node("the_asset") == 5


def test_resource_annotations():
    @dg.asset
    def the_asset(
        context: dg.AssetExecutionContext,
        my_resource: MyResource,
        raw_resource: dg.ResourceParam[RawResource],
    ) -> int:
        assert isinstance(context, dg.AssetExecutionContext)
        return my_resource.value + raw_resource.value

    assert {arg.name for arg in the_asset.op.compute_fn.get_resource_args()} == {  # pyright: ignore[reportAttributeAccessIssue]
        "my_resource",
        "raw_resource",
    }

    result = dg.materialize(
        [the_asset],
        resources={"my_resource": MyResource(value=1), "raw_resource": RawResource(value=2)},
    )
    assert result.output_for_node("the_asset") == 3


def test_input_and_output_annotations():
    @dg.asset
    def upstream() -> int:
        return 1

    @dg.asset
    def downstream(context: dg.AssetExecutionContext, upstream: int) -> str:
        return str(upstream)

    assert downstream.op.ins["upstream"].dagster_type.typing_type is int
    assert downstream.op.outs["result"].dagster_type.typing_type is str

    result = dg.materialize([upstream, downstream])
    assert result.output_for_node("downstream") == "1"
