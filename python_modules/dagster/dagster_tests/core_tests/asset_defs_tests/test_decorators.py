import warnings

import pytest

from dagster import (
    AssetKey,
    AssetOut,
    DagsterInvalidDefinitionError,
    OpExecutionContext,
    Out,
    Output,
    StaticPartitionsDefinition,
    String,
)
from dagster import _check as check
from dagster import build_op_context, io_manager, resource
from dagster._core.definitions import AssetIn, AssetsDefinition, asset, build_assets_job, multi_asset
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied


@pytest.fixture(autouse=True)
def check_experimental_warnings():
    with warnings.catch_warnings(record=True) as record:
        yield

        for w in record:
            if "asset_key" in w.message.args[0]:
                assert False, f"Unexpected warning: {w.message.args[0]}"


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
    assert AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_asset_with_config_schema():
    @asset(config_schema={"foo": int})
    def my_asset(arg1):
        return arg1

    assert my_asset.op.config_schema


def test_multi_asset_with_config_schema():
    @multi_asset(outs={"o1": AssetOut()}, config_schema={"foo": int})
    def my_asset(arg1):
        return arg1

    assert my_asset.op.config_schema


def test_asset_with_compute_kind():
    @asset(compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_with_compute_kind():
    @multi_asset(outs={"o1": AssetOut()}, compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_out_name_diff_from_asset_key():
    @multi_asset(
        outs={
            "my_out_name": AssetOut(key=AssetKey("my_asset_name")),
            "my_other_out_name": AssetOut(key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.keys == {AssetKey("my_asset_name"), AssetKey("my_other_asset")}


def test_multi_asset_key_prefix():
    @multi_asset(
        outs={
            "my_asset_name": AssetOut(key_prefix="prefix1"),
            "my_other_asset": AssetOut(key_prefix="prefix2"),
        }
    )
    def my_asset():
        yield Output(1, "my_asset_name")
        yield Output(2, "my_other_asset")

    assert my_asset.keys == {
        AssetKey(["prefix1", "my_asset_name"]),
        AssetKey(["prefix2", "my_other_asset"]),
    }


def test_multi_asset_out_backcompat():
    @multi_asset(
        outs={
            "my_out_name": Out(asset_key=AssetKey("my_asset_name")),
            "my_other_out_name": Out(asset_key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.keys == {AssetKey("my_asset_name"), AssetKey("my_other_asset")}


def test_multi_asset_infer_from_empty_asset_key():
    @multi_asset(outs={"my_out_name": AssetOut(), "my_other_out_name": AssetOut()})
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}


def test_multi_asset_group_names():
    @multi_asset(
        outs={
            "out1": AssetOut(group_name="foo", key=AssetKey(["cool", "key1"])),
            "out2": Out(),
            "out3": AssetOut(),
            "out4": AssetOut(group_name="bar", key_prefix="prefix4"),
            "out5": AssetOut(group_name="bar"),
        }
    )
    def my_asset():
        pass

    assert my_asset.group_names_by_key == {
        AssetKey(["cool", "key1"]): "foo",
        AssetKey("out2"): "default",
        AssetKey("out3"): "default",
        AssetKey(["prefix4", "out4"]): "bar",
        AssetKey("out5"): "bar",
    }


def test_multi_asset_group_name():
    @multi_asset(
        outs={
            "out1": AssetOut(key=AssetKey(["cool", "key1"])),
            "out2": Out(),
            "out3": AssetOut(),
            "out4": AssetOut(key_prefix="prefix4"),
            "out5": AssetOut(),
        },
        group_name="bar",
    )
    def my_asset():
        pass

    assert my_asset.group_names_by_key == {
        AssetKey(["cool", "key1"]): "bar",
        AssetKey("out2"): "bar",
        AssetKey("out3"): "bar",
        AssetKey(["prefix4", "out4"]): "bar",
        AssetKey("out5"): "bar",
    }


def test_multi_asset_group_names_and_group_name():
    with pytest.raises(check.CheckError):

        @multi_asset(
            outs={
                "out1": AssetOut(group_name="foo", key=AssetKey(["cool", "key1"])),
                "out2": Out(),
                "out3": AssetOut(),
                "out4": AssetOut(group_name="bar", key_prefix="prefix4"),
                "out5": AssetOut(group_name="bar"),
            },
            group_name="something",
        )
        def my_asset():
            pass


def test_multi_asset_internal_asset_deps_metadata():
    @multi_asset(
        outs={
            "my_out_name": AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {AssetKey("my_other_out_name"), AssetKey("my_in_name")},
            "my_other_out_name": {AssetKey("my_in_name")},
        },
    )
    def my_asset(my_in_name):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}
    assert my_asset.op.output_def_named("my_out_name").metadata == {"foo": "bar"}
    assert my_asset.op.output_def_named("my_other_out_name").metadata == {"bar": "foo"}
    assert my_asset.asset_deps == {
        AssetKey("my_out_name"): {AssetKey("my_other_out_name"), AssetKey("my_in_name")},
        AssetKey("my_other_out_name"): {AssetKey("my_in_name")},
    }


def test_multi_asset_internal_asset_deps_invalid():

    with pytest.raises(check.CheckError, match="Invalid out key"):

        @multi_asset(
            outs={"my_out_name": AssetOut()},
            internal_asset_deps={"something_weird": {AssetKey("my_out_name")}},
        )
        def _my_asset():
            pass

    with pytest.raises(check.CheckError, match="Invalid asset dependencies"):

        @multi_asset(
            outs={"my_out_name": AssetOut()},
            internal_asset_deps={"my_out_name": {AssetKey("something_weird")}},
        )
        def _my_asset():
            pass


def test_asset_with_dagster_type():
    @asset(dagster_type=String)
    def my_asset(arg1):
        return arg1

    assert my_asset.op.output_defs[0].dagster_type.display_name == "String"


def test_asset_with_key_prefix():
    @asset(key_prefix="my_key_prefix")
    def my_asset():
        pass

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0
    assert my_asset.op.name == "my_key_prefix__my_asset"
    assert my_asset.keys == {AssetKey(["my_key_prefix", "my_asset"])}

    @asset(key_prefix=["one", "two", "three"])
    def multi_component_list_asset():
        pass

    assert isinstance(multi_component_list_asset, AssetsDefinition)
    assert len(multi_component_list_asset.op.output_defs) == 1
    assert len(multi_component_list_asset.op.input_defs) == 0
    assert multi_component_list_asset.op.name == "one__two__three__multi_component_list_asset"
    assert multi_component_list_asset.keys == {
        AssetKey(["one", "two", "three", "multi_component_list_asset"])
    }

    @asset(key_prefix=["one", "two", "three"])
    def multi_component_str_asset():
        pass

    assert isinstance(multi_component_str_asset, AssetsDefinition)
    assert len(multi_component_str_asset.op.output_defs) == 1
    assert len(multi_component_str_asset.op.input_defs) == 0
    assert multi_component_str_asset.op.name == "one__two__three__multi_component_str_asset"
    assert multi_component_str_asset.keys == {
        AssetKey(["one", "two", "three", "multi_component_str_asset"])
    }


def test_asset_with_namespace():

    with pytest.warns(DeprecationWarning):

        @asset(namespace="my_namespace")
        def my_asset():
            pass

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0
    assert my_asset.op.name == "my_namespace__my_asset"
    assert my_asset.keys == {AssetKey(["my_namespace", "my_asset"])}

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
    assert multi_component_namespace_asset.keys == {
        AssetKey(["one", "two", "three", "multi_component_namespace_asset"])
    }


def test_asset_with_inputs_and_key_prefix():
    @asset(key_prefix="my_prefix")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    # this functions differently than the namespace arg in this scenario
    assert AssetKey(["my_prefix", "arg1"]) not in my_asset.keys_by_input_name.values()
    assert AssetKey(["arg1"]) in my_asset.keys_by_input_name.values()


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
    assert AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_input_asset_key():
    @asset(ins={"arg1": AssetIn(key=AssetKey("foo"))})
    def my_asset(arg1):
        assert arg1

    assert AssetKey("foo") in my_asset.keys_by_input_name.values()


def test_input_asset_key_and_key_prefix():
    with pytest.raises(check.CheckError, match="key and key_prefix cannot both be set"):

        @asset(ins={"arg1": AssetIn(key=AssetKey("foo"), key_prefix="bar")})
        def _my_asset(arg1):
            assert arg1


def test_input_namespace_str():
    @asset(ins={"arg1": AssetIn(namespace="abc")})
    def my_asset(arg1):
        assert arg1

    assert AssetKey(["abc", "arg1"]) in my_asset.keys_by_input_name.values()


def test_input_namespace_list():
    @asset(ins={"arg1": AssetIn(namespace=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert AssetKey(["abc", "xyz", "arg1"]) in my_asset.keys_by_input_name.values()


def test_input_key_prefix_str():
    @asset(ins={"arg1": AssetIn(key_prefix=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert AssetKey(["abc", "xyz", "arg1"]) in my_asset.keys_by_input_name.values()


def test_input_key_prefix_list():
    @asset(ins={"arg1": AssetIn(key_prefix=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert AssetKey(["abc", "xyz", "arg1"]) in my_asset.keys_by_input_name.values()


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
    def arg_kwarg_asset(arg1, kwarg1=None):
        kwarg1 = kwarg1 or [0]
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


def test_op_tags():
    tags = {"apple": "banana", "orange": {"rind": "fsd", "segment": "fjdskl"}}
    tags_stringified = {"apple": "banana", "orange": '{"rind": "fsd", "segment": "fjdskl"}'}

    @asset(op_tags=tags)
    def my_asset():
        ...

    assert my_asset.op.tags == tags_stringified


def test_kwargs():
    @asset(ins={"upstream": AssetIn()})
    def my_asset(**kwargs):
        del kwargs

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("upstream") in my_asset.keys_by_input_name.values()


def test_multi_asset_resource_defs():
    @resource
    def baz_resource():
        pass

    @io_manager(required_resource_keys={"baz"})
    def foo_manager():
        pass

    @io_manager
    def bar_manager():
        pass

    @multi_asset(
        outs={
            "key1": Out(asset_key=AssetKey("key1"), io_manager_key="foo"),
            "key2": Out(asset_key=AssetKey("key2"), io_manager_key="bar"),
        },
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"foo", "bar", "baz"}

    ensure_requirements_satisfied(
        my_asset.resource_defs, list(my_asset.get_resource_requirements())
    )


def test_asset_io_manager_def():
    @io_manager
    def the_manager():
        pass

    @asset(io_manager_def=the_manager)
    def the_asset():
        pass

    # If IO manager def is passed directly, then it doesn't appear as a
    # required resource key on the underlying op.
    assert set(the_asset.node_def.required_resource_keys) == set()

    @asset(io_manager_key="blah", resource_defs={"blah": the_manager})
    def other_asset():
        pass

    # If IO manager def is provided as a resource def, it appears in required
    # resource keys on the underlying op.
    assert set(other_asset.node_def.required_resource_keys) == {"blah"}
