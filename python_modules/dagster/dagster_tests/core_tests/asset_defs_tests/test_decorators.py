import warnings

import pytest

from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    GraphIn,
    GraphOut,
    In,
    Nothing,
    OpExecutionContext,
    Out,
    Output,
    String,
    build_op_context,
    check,
    graph,
    op,
    resource,
)
from dagster.core.asset_defs import AssetIn, AssetsDefinition, asset, build_assets_job, multi_asset
from dagster.core.asset_defs.decorators import ASSET_DEPENDENCY_METADATA_KEY, assets_definition
from dagster.utils.backcompat import ExperimentalWarning


@pytest.fixture(autouse=True)
def check_experimental_warnings():
    with warnings.catch_warnings(record=True) as record:
        yield

        raises_warning = False
        for w in record:
            if "asset_key" in w.message.args[0]:
                raises_warning = True
                break

        assert not raises_warning


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
    assert my_asset.input_asset_keys == {AssetKey("arg1")}


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


@pytest.mark.skip(reason="Temporarily disable this behavior")
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
            AssetKey("my_out_name"): {AssetKey("my_other_out_name"), AssetKey("my_in_name")},
            AssetKey("my_other_out_name"): {AssetKey("my_in_name")},
        },
    )
    def my_asset(my_in_name):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}
    assert my_asset.op.output_def_named("my_out_name").metadata == {"foo": "bar"}
    assert my_asset.op.output_def_named("my_other_out_name").metadata == {"bar": "foo"}


def test_multi_asset_internal_asset_deps_invalid():

    with pytest.raises(check.CheckError, match="Invariant failed"):

        @multi_asset(
            outs={"my_out_name": Out()},
            internal_asset_deps={AssetKey("something_weird"): {AssetKey("my_out_name")}},
        )
        def _my_asset():
            pass

    with pytest.raises(check.CheckError, match="Invariant failed"):

        @multi_asset(
            outs={"my_out_name": Out()},
            internal_asset_deps={AssetKey("my_out_name"): {AssetKey("something_weird")}},
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
    assert my_asset.input_asset_keys == {AssetKey(["my_namespace", "arg1"])}


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
    assert my_asset.input_asset_keys == {AssetKey("arg1")}
    assert my_asset.asset_keys == {AssetKey("my_asset")}


def test_input_asset_key():
    @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"))})
    def my_asset(arg1):
        assert arg1

    assert my_asset.input_asset_keys == {AssetKey("foo")}


def test_input_asset_key_and_namespace():
    with pytest.raises(check.CheckError, match="key and namespace cannot both be set"):

        @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"), namespace="bar")})
        def _my_asset(arg1):
            assert arg1


def test_input_namespace_str():
    @asset(ins={"arg1": AssetIn(namespace="abc")})
    def my_asset(arg1):
        assert arg1

    assert my_asset.input_asset_keys == {AssetKey(["abc", "arg1"])}


def test_input_namespace_list():
    @asset(ins={"arg1": AssetIn(namespace=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert my_asset.input_asset_keys == {AssetKey(["abc", "xyz", "arg1"])}


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

def test_partitions_def():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    assert my_asset.partitions_def == partitions_def


def test_asset_definition_decorator():
    @assets_definition(
        asset_keys_by_input_name={"x": AssetKey("x_asset"), "y": AssetKey("y_asset")},
        asset_keys_by_output_name={"a": AssetKey("a_asset"), "b": AssetKey("b_asset")},
    )
    @op(out={"a": Out(), "b": Out()}, ins={"x": In(int), "y": In(int)})
    def multi_asset_op(context, x, y):
        yield Output(1, "a")
        yield Output(2, "b")

    output_def_by_asset_key = multi_asset_op.output_defs_by_asset_key
    input_def_by_asset_key = multi_asset_op.input_defs_by_asset_key

    assert output_def_by_asset_key[AssetKey("a_asset")].name == "a"
    assert output_def_by_asset_key[AssetKey("b_asset")].name == "b"
    assert input_def_by_asset_key[AssetKey("x_asset")].name == "x"
    assert input_def_by_asset_key[AssetKey("y_asset")].name == "y"


def test_asset_definition_no_names_specified():
    @assets_definition
    @op(out={"a": Out(), "b": Out()}, ins={"x": In(int), "y": In(int), "z": In(Nothing)})
    def multi_asset_op(context, x, y):
        yield Output(1, "a")
        yield Output(2, "b")

    output_def_by_asset_key = multi_asset_op.output_defs_by_asset_key
    input_def_by_asset_key = multi_asset_op.input_defs_by_asset_key

    assert output_def_by_asset_key[AssetKey("a")].name == "a"
    assert output_def_by_asset_key[AssetKey("b")].name == "b"
    assert input_def_by_asset_key[AssetKey("x")].name == "x"
    assert input_def_by_asset_key[AssetKey("y")].name == "y"
    assert input_def_by_asset_key[AssetKey("z")].name == "z"


def test_assets_no_ins_outs():
    @assets_definition(asset_keys_by_input_name={"x": AssetKey("x_asset")})
    @op
    def multi_asset_op(context, x, y):
        yield Output(1, "a")
        yield Output(2, "b")

    input_def_by_asset_key = multi_asset_op.input_defs_by_asset_key
    assert input_def_by_asset_key[AssetKey("x_asset")].name == "x"
    assert input_def_by_asset_key[AssetKey("y")].name == "y"


def test_partial_asset_keys_provided():
    @assets_definition(
        asset_keys_by_input_name={"x": AssetKey("x_asset")},
        asset_keys_by_output_name={"a": AssetKey("a_asset")},
    )
    @op(out={"a": Out(), "b": Out()}, ins={"x": In(int), "y": In(int), "z": In(Nothing)})
    def multi_asset_op(context, x, y):
        yield Output(1, "a")
        yield Output(2, "b")

    output_def_by_asset_key = multi_asset_op.output_defs_by_asset_key
    input_def_by_asset_key = multi_asset_op.input_defs_by_asset_key

    assert output_def_by_asset_key[AssetKey("a_asset")].name == "a"
    assert output_def_by_asset_key[AssetKey("b")].name == "b"
    assert input_def_by_asset_key[AssetKey("x_asset")].name == "x"
    assert input_def_by_asset_key[AssetKey("y")].name == "y"


def test_default_assets_and_op_definition():
    @assets_definition(asset_keys_by_output_name={"result": AssetKey("result_asset")})
    @op
    def my_op():
        return 5, 6

    output_def_by_asset_key = my_op.output_defs_by_asset_key
    input_def_by_asset_key = my_op.input_defs_by_asset_key

    assert input_def_by_asset_key == {}
    assert output_def_by_asset_key[AssetKey("result_asset")].name == "result"


def test_assets_definition_errors_when_not_op_decorated():
    with pytest.raises(Exception):

        @assets_definition
        @resource
        def my_op():
            return 5, 6

    with pytest.raises(Exception):

        @assets_definition(asset_keys_by_output_name={"result": AssetKey("result_asset")})
        @resource
        def my_op():
            return 5, 6


def test_internal_asset_deps():
    with pytest.raises(Exception):

        @assets_definition(internal_asset_deps={"non_exist_output_name": AssetKey("b")})
        @op(out={"a": Out(), "b": Out()})
        def multi_asset_op(context):
            yield Output(1, "a")
            yield Output(2, "b")

def _invert_dict(input_dict):
    return {value: key for key, value in input_dict.items()}

def test_graph_asset_decorator_inputs():
    @op
    def my_op(x, y):
        return x

    @assets_definition(asset_keys_by_input_name={"x": AssetKey("x_asset")})
    @graph(ins={"x": GraphIn()})
    def my_graph(x, y):
        my_op(x, y)

    input_defs_by_asset_key = _invert_dict(my_graph.asset_keys_by_input_def)
    assert input_defs_by_asset_key[AssetKey("x_asset")].name == "x"
    assert input_defs_by_asset_key[AssetKey("y")].name == "y"

def test_graph_asset_decorator_outputs():
    @op
    def x_op(x):
        return x

    @op
    def y_op(y):
        return y

    @assets_definition(asset_keys_by_output_name={"y": AssetKey("y_asset")})
    @graph(out={"x": GraphOut(), "y": GraphOut()})
    def my_graph(x, y):
        return {"x": x_op(x), "y": y_op(y)}

    output_defs_by_asset_key = _invert_dict(my_graph.asset_keys_by_output_def)
    assert output_defs_by_asset_key[AssetKey("y_asset")].name == "y"
    assert output_defs_by_asset_key[AssetKey("x")].name == "x"

def test_graph_asset_decorator_no_args():
    @op
    def my_op(x, y):
        return x

    @assets_definition
    @graph
    def my_graph(x, y):
        return my_op(x, y)

    input_defs_by_asset_key = _invert_dict(my_graph.asset_keys_by_input_def)
    output_defs_by_asset_key = _invert_dict(my_graph.asset_keys_by_output_def)
    assert input_defs_by_asset_key[AssetKey("x")].name == "x"
    assert input_defs_by_asset_key[AssetKey("y")].name == "y"
    assert output_defs_by_asset_key[AssetKey("result")].name == "result"