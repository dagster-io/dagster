import pytest

from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    OpExecutionContext,
    Out,
    Output,
    String,
    build_op_context,
    check,
)
from dagster.core.asset_defs import AssetIn, AssetsDefinition, asset, build_assets_job, multi_asset
from dagster.core.asset_defs.decorators import ASSET_DEPENDENCY_METADATA_KEY


def test_asset_no_decorator_args():
    @asset
    def my_asset():
        return 1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_inputs():
    @asset
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_asset_with_compute_kind():
    @asset(compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_with_compute_kind():
    @multi_asset(outs={"o1": Out(asset_key=AssetKey("o1"))}, compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_out_name_diff_from_asset_key():
    @multi_asset(
        outs={
            "my_out_name": Out(asset_key=AssetKey("my_asset_name")),
            "my_other_out_name": Out(asset_key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_asset_name"), AssetKey("my_other_asset")}


def test_multi_asset_infer_from_empty_asset_key():
    @multi_asset(outs={"my_out_name": Out(), "my_other_out_name": Out()})
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}


def test_multi_asset_internal_asset_deps_metadata():
    @multi_asset(
        outs={
            "my_out_name": Out(metadata={"foo": "bar"}),
            "my_other_out_name": Out(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {AssetKey("my_other_out_name"), AssetKey("my_in_name")}
        },
    )
    def my_asset(my_in_name):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}
    assert my_asset.op.output_def_named("my_out_name").metadata == {
        "foo": "bar",
        ASSET_DEPENDENCY_METADATA_KEY: {AssetKey("my_other_out_name"), AssetKey("my_in_name")},
    }
    assert my_asset.op.output_def_named("my_other_out_name").metadata == {"bar": "foo"}


def test_multi_asset_internal_asset_deps_invalid():

    with pytest.raises(check.CheckError, match="Invalid out key"):

        @multi_asset(
            outs={"my_out_name": Out()},
            internal_asset_deps={"something_weird": {AssetKey("my_out_name")}},
        )
        def _my_asset():
            pass

    with pytest.raises(check.CheckError, match="Invalid asset dependencies"):

        @multi_asset(
            outs={"my_out_name": Out()},
            internal_asset_deps={"my_out_name": {AssetKey("something_weird")}},
        )
        def _my_asset():
            pass


def test_asset_with_dagster_type():
    @asset(dagster_type=String)
    def my_asset(arg1):
        return arg1

    assert my_asset.op.output_defs[0].dagster_type.display_name == "String"


def test_asset_with_namespace():
    @asset(namespace="my_namespace")
    def my_asset():
        pass

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0
    assert my_asset.op.name == "my_namespace__my_asset"
    assert my_asset.asset_keys == {AssetKey(["my_namespace", "my_asset"])}

    @asset(namespace=["one", "two", "three"])
    def multi_component_namespace_asset():
        pass

    assert isinstance(multi_component_namespace_asset, AssetsDefinition)
    assert len(multi_component_namespace_asset.op.output_defs) == 1
    assert len(multi_component_namespace_asset.op.input_defs) == 0
    assert (
        multi_component_namespace_asset.op.name
        == "one__two__three__multi_component_namespace_asset"
    )
    assert multi_component_namespace_asset.asset_keys == {
        AssetKey(["one", "two", "three", "multi_component_namespace_asset"])
    }


def test_asset_with_inputs_and_namespace():
    @asset(namespace="my_namespace")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey(["my_namespace", "arg1"])


def test_asset_with_context_arg():
    @asset
    def my_asset(context):
        context.log("hello")

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_context_arg_and_dep():
    @asset
    def my_asset(context, arg1):
        context.log("hello")
        assert arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_input_asset_key():
    @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"))})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("foo")


def test_input_asset_key_and_namespace():
    with pytest.raises(check.CheckError, match="key and namespace cannot both be set"):

        @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"), namespace="bar")})
        def _my_asset(arg1):
            assert arg1


def test_input_namespace_str():
    @asset(ins={"arg1": AssetIn(namespace="abc")})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey(["abc", "arg1"])


def test_input_namespace_list():
    @asset(ins={"arg1": AssetIn(namespace=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey(["abc", "xyz", "arg1"])


def test_input_metadata():
    @asset(ins={"arg1": AssetIn(metadata={"abc": 123})})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].metadata == {"abc": 123}


def test_unknown_in():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(ins={"arg1": AssetIn()})
        def _my_asset():
            pass


def test_all_fields():
    @asset(
        required_resource_keys={"abc", "123"},
        io_manager_key="my_io_key",
        description="some description",
        metadata={"metakey": "metaval"},
    )
    def my_asset():
        pass

    assert my_asset.op.required_resource_keys == {"abc", "123"}
    assert my_asset.op.description == "some description"
    assert len(my_asset.op.output_defs) == 1
    output_def = my_asset.op.output_defs[0]
    assert output_def.io_manager_key == "my_io_key"
    assert output_def.metadata["metakey"] == "metaval"


def test_infer_input_dagster_type():
    @asset
    def my_asset(_input1: str):
        pass

    assert my_asset.op.input_defs[0].dagster_type.display_name == "String"


def test_invoking_simple_assets():
    @asset
    def no_input_asset():
        return [1, 2, 3]

    out = no_input_asset()
    assert out == [1, 2, 3]

    @asset
    def arg_input_asset(arg1, arg2):
        return arg1 + arg2

    out = arg_input_asset([1, 2, 3], [4, 5, 6])
    assert out == [1, 2, 3, 4, 5, 6]

    @asset
    def arg_kwarg_asset(arg1, kwarg1=[0]):
        return arg1 + kwarg1

    out = arg_kwarg_asset([1, 2, 3], kwarg1=[3, 2, 1])
    assert out == [1, 2, 3, 3, 2, 1]

    out = arg_kwarg_asset(([1, 2, 3]))
    assert out == [1, 2, 3, 0]


def test_invoking_asset_with_deps():
    @asset
    def upstream():
        return [1]

    @asset
    def downstream(upstream):
        return upstream + [2, 3]

    # check that the asset dependencies are in place
    job = build_assets_job("foo", [upstream, downstream])
    assert job.execute_in_process().success

    out = downstream([3])
    assert out == [3, 2, 3]


def test_invoking_asset_with_context():
    @asset
    def asset_with_context(context, arg1):
        assert isinstance(context, OpExecutionContext)
        return arg1

    ctx = build_op_context()
    out = asset_with_context(ctx, 1)
    assert out == 1
