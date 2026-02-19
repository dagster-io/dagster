from typing import Any

import dagster as dg
import pytest
from dagster import (
    Nothing,
    String,
    _check as check,
)
from dagster._check import CheckError
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.definitions.tags import build_kind_tag
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._core.test_utils import ignore_warning, raise_exception_on_warnings
from dagster._core.types.dagster_type import resolve_dagster_type


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def test_asset_no_decorator_args():
    @dg.asset
    def my_asset():
        return 1

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_inputs():
    @dg.asset
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_asset_no_decorator_args_direct_call():
    def func():
        return 1

    my_asset = dg.asset(func)

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_inputs_direct_call():
    def func(arg1):
        return arg1

    my_asset = dg.asset(func)

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_asset_with_config_schema():
    @dg.asset(config_schema={"foo": int})
    def my_asset(context):
        assert context.op_execution_context.op_config["foo"] == 5

    dg.materialize_to_memory([my_asset], run_config={"ops": {"my_asset": {"config": {"foo": 5}}}})

    with pytest.raises(dg.DagsterInvalidConfigError):
        dg.materialize_to_memory([my_asset])


def test_multi_asset_with_config_schema():
    @dg.multi_asset(outs={"o1": dg.AssetOut()}, config_schema={"foo": int})
    def my_asset(context):
        assert context.op_execution_context.op_config["foo"] == 5

    dg.materialize_to_memory([my_asset], run_config={"ops": {"my_asset": {"config": {"foo": 5}}}})

    with pytest.raises(dg.DagsterInvalidConfigError):
        dg.materialize_to_memory([my_asset])


def test_asset_with_compute_kind():
    @dg.asset(compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {COMPUTE_KIND_TAG: "sql"}


def test_multi_asset_with_compute_kind():
    @dg.multi_asset(outs={"o1": dg.AssetOut()}, compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {COMPUTE_KIND_TAG: "sql"}


def test_multi_asset_out_name_diff_from_asset_key():
    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(key=dg.AssetKey("my_asset_name")),
            "my_other_out_name": dg.AssetOut(key=dg.AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    assert my_asset.keys == {dg.AssetKey("my_asset_name"), dg.AssetKey("my_other_asset")}


def test_multi_asset_key_prefix():
    @dg.multi_asset(
        outs={
            "my_asset_name": dg.AssetOut(key_prefix="prefix1"),
            "my_other_asset": dg.AssetOut(key_prefix="prefix2"),
        }
    )
    def my_asset():
        yield dg.Output(1, "my_asset_name")
        yield dg.Output(2, "my_other_asset")

    assert my_asset.keys == {
        dg.AssetKey(["prefix1", "my_asset_name"]),
        dg.AssetKey(["prefix2", "my_other_asset"]),
    }


def test_multi_asset_out_backcompat():
    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(key=dg.AssetKey("my_asset_name")),
            "my_other_out_name": dg.AssetOut(key=dg.AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    assert my_asset.keys == {dg.AssetKey("my_asset_name"), dg.AssetKey("my_other_asset")}


def test_multi_asset_infer_from_empty_asset_key():
    @dg.multi_asset(outs={"my_out_name": dg.AssetOut(), "my_other_out_name": dg.AssetOut()})
    def my_asset():
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    assert my_asset.keys == {dg.AssetKey("my_out_name"), dg.AssetKey("my_other_out_name")}


def test_multi_asset_group_names():
    @dg.multi_asset(
        outs={
            "out1": dg.AssetOut(group_name="foo", key=dg.AssetKey(["cool", "key1"])),
            "out2": dg.AssetOut(),
            "out3": dg.AssetOut(),
            "out4": dg.AssetOut(group_name="bar", key_prefix="prefix4"),
            "out5": dg.AssetOut(group_name="bar"),
        }
    )
    def my_asset():
        pass

    assert my_asset.group_names_by_key == {
        dg.AssetKey(["cool", "key1"]): "foo",
        dg.AssetKey("out2"): "default",
        dg.AssetKey("out3"): "default",
        dg.AssetKey(["prefix4", "out4"]): "bar",
        dg.AssetKey("out5"): "bar",
    }


def test_multi_asset_group_name():
    @dg.multi_asset(
        outs={
            "out1": dg.AssetOut(key=dg.AssetKey(["cool", "key1"])),
            "out2": dg.AssetOut(),
            "out3": dg.AssetOut(),
            "out4": dg.AssetOut(key_prefix="prefix4"),
            "out5": dg.AssetOut(),
        },
        group_name="bar",
    )
    def my_asset():
        pass

    assert my_asset.group_names_by_key == {
        dg.AssetKey(["cool", "key1"]): "bar",
        dg.AssetKey("out2"): "bar",
        dg.AssetKey("out3"): "bar",
        dg.AssetKey(["prefix4", "out4"]): "bar",
        dg.AssetKey("out5"): "bar",
    }


def test_multi_asset_group_names_and_group_name():
    with pytest.raises(check.CheckError):

        @dg.multi_asset(
            outs={
                "out1": dg.AssetOut(group_name="foo", key=dg.AssetKey(["cool", "key1"])),
                "out2": dg.AssetOut(),
                "out3": dg.AssetOut(),
                "out4": dg.AssetOut(group_name="bar", key_prefix="prefix4"),
                "out5": dg.AssetOut(group_name="bar"),
            },
            group_name="something",
        )
        def my_asset():
            pass


def test_multi_asset_internal_asset_deps_metadata():
    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": dg.AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {dg.AssetKey("my_other_out_name"), dg.AssetKey("my_in_name")},
            "my_other_out_name": {dg.AssetKey("my_in_name")},
        },
    )
    def my_asset(my_in_name):
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    assert my_asset.keys == {dg.AssetKey("my_out_name"), dg.AssetKey("my_other_out_name")}
    assert my_asset.op.output_def_named("my_out_name").metadata == {"foo": "bar"}
    assert my_asset.op.output_def_named("my_other_out_name").metadata == {"bar": "foo"}
    assert my_asset.asset_deps == {
        dg.AssetKey("my_out_name"): {dg.AssetKey("my_other_out_name"), dg.AssetKey("my_in_name")},
        dg.AssetKey("my_other_out_name"): {dg.AssetKey("my_in_name")},
    }


def test_multi_asset_internal_asset_deps_invalid():
    with pytest.raises(check.CheckError, match="Invalid out key"):

        @dg.multi_asset(
            outs={"my_out_name": dg.AssetOut()},
            internal_asset_deps={"something_weird": {dg.AssetKey("my_out_name")}},
        )
        def _my_asset():
            pass

    with pytest.raises(check.CheckError, match="Invalid asset dependencies"):

        @dg.multi_asset(
            outs={"my_out_name": dg.AssetOut()},
            internal_asset_deps={"my_out_name": {dg.AssetKey("something_weird")}},
        )
        def _my_asset():
            pass


def test_asset_with_dagster_type():
    @dg.asset(dagster_type=String)  # pyright: ignore[reportArgumentType]
    def my_asset(arg1):
        return arg1

    assert my_asset.op.output_defs[0].dagster_type.display_name == "String"


@ignore_warning("Property `OpDefinition.version` is deprecated")
def test_asset_with_code_version():
    @dg.asset(code_version="foo")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.version == "foo"
    assert my_asset.op.output_def_named("result").code_version == "foo"


@ignore_warning("Property `OpDefinition.version` is deprecated")
def test_asset_with_code_version_direct_call():
    def func(arg1):
        return arg1

    my_asset = dg.asset(func, code_version="foo")

    assert my_asset.op.version == "foo"
    assert my_asset.op.output_def_named("result").code_version == "foo"


def test_asset_with_key_prefix():
    @dg.asset(key_prefix="my_key_prefix")
    def my_asset():
        pass

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0
    assert my_asset.op.name == "my_key_prefix__my_asset"
    assert my_asset.keys == {dg.AssetKey(["my_key_prefix", "my_asset"])}

    @dg.asset(key_prefix=["one", "two", "three"])
    def multi_component_list_asset():
        pass

    assert isinstance(multi_component_list_asset, dg.AssetsDefinition)
    assert len(multi_component_list_asset.op.output_defs) == 1
    assert len(multi_component_list_asset.op.input_defs) == 0
    assert multi_component_list_asset.op.name == "one__two__three__multi_component_list_asset"
    assert multi_component_list_asset.keys == {
        dg.AssetKey(["one", "two", "three", "multi_component_list_asset"])
    }

    @dg.asset(key_prefix=["one", "two", "three"])
    def multi_component_str_asset():
        pass

    assert isinstance(multi_component_str_asset, dg.AssetsDefinition)
    assert len(multi_component_str_asset.op.output_defs) == 1
    assert len(multi_component_str_asset.op.input_defs) == 0
    assert multi_component_str_asset.op.name == "one__two__three__multi_component_str_asset"
    assert multi_component_str_asset.keys == {
        dg.AssetKey(["one", "two", "three", "multi_component_str_asset"])
    }


def test_asset_with_inputs_and_key_prefix():
    @dg.asset(key_prefix="my_prefix")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    # this functions differently than the key_prefix arg in this scenario
    assert dg.AssetKey(["my_prefix", "arg1"]) not in my_asset.keys_by_input_name.values()
    assert dg.AssetKey(["arg1"]) in my_asset.keys_by_input_name.values()


def test_asset_with_context_arg():
    @dg.asset
    def my_asset(context):
        context.log("hello")

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_context_arg_and_dep():
    @dg.asset
    def my_asset(context, arg1):
        context.log("hello")
        assert arg1

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_input_asset_key():
    @dg.asset(ins={"arg1": dg.AssetIn(key=dg.AssetKey("foo"))})
    def my_asset(arg1):
        assert arg1

    assert dg.AssetKey("foo") in my_asset.keys_by_input_name.values()


def test_input_asset_key_and_key_prefix():
    with pytest.raises(check.CheckError, match="key and key_prefix cannot both be set"):

        @dg.asset(ins={"arg1": dg.AssetIn(key=dg.AssetKey("foo"), key_prefix="bar")})
        def _my_asset(arg1):
            assert arg1


def test_input_key_prefix_str():
    @dg.asset(ins={"arg1": dg.AssetIn(key_prefix="abc")})
    def my_asset(arg1):
        assert arg1

    assert dg.AssetKey(["abc", "arg1"]) in my_asset.keys_by_input_name.values()


def test_input_key_prefix_list():
    @dg.asset(ins={"arg1": dg.AssetIn(key_prefix=["abc", "xyz"])})
    def my_asset(arg1):
        assert arg1

    assert dg.AssetKey(["abc", "xyz", "arg1"]) in my_asset.keys_by_input_name.values()


def test_input_metadata():
    @dg.asset(ins={"arg1": dg.AssetIn(metadata={"abc": 123})})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].metadata == {"abc": 123}


def test_input_dagster_type():
    my_dagster_type = resolve_dagster_type(str)

    @dg.asset(ins={"arg1": dg.AssetIn(dagster_type=my_dagster_type)})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.ins["arg1"].dagster_type == my_dagster_type


def test_unknown_in():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.asset(ins={"arg1": dg.AssetIn()})
        def _my_asset():
            pass


def test_all_fields():
    @dg.asset(
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
    @dg.asset
    def my_asset(_input1: str):
        pass

    assert my_asset.op.input_defs[0].dagster_type.display_name == "String"
    assert my_asset.op.input_defs[0].dagster_type.typing_type == str


def test_infer_output_dagster_type():
    @dg.asset
    def my_asset() -> str:
        return "foo"

    assert my_asset.op.outs["result"].dagster_type.display_name == "String"  # pyright: ignore[reportAttributeAccessIssue]
    assert my_asset.op.outs["result"].dagster_type.typing_type == str  # pyright: ignore[reportAttributeAccessIssue]


def test_infer_output_dagster_type_none():
    @dg.asset
    def my_asset() -> None:
        pass

    assert my_asset.op.outs["result"].dagster_type.typing_type == type(None)  # pyright: ignore[reportAttributeAccessIssue]
    assert my_asset.op.outs["result"].dagster_type.display_name == "Nothing"  # pyright: ignore[reportAttributeAccessIssue]


def test_infer_output_dagster_type_empty():
    @dg.asset
    def my_asset():
        pass

    assert my_asset.op.outs["result"].dagster_type.typing_type is Any  # pyright: ignore[reportAttributeAccessIssue]
    assert my_asset.op.outs["result"].dagster_type.display_name == "Any"  # pyright: ignore[reportAttributeAccessIssue]


def test_asset_with_docstring_description():
    @dg.asset
    def asset1():
        """Docstring."""
        pass

    assert asset1.op.description == "Docstring."


def test_asset_with_parameter_description():
    @dg.asset(description="parameter")
    def asset1():
        pass

    assert asset1.op.description == "parameter"


def test_asset_with_docstring_and_parameter_description():
    @dg.asset(description="parameter")
    def asset1():
        """Docstring."""
        pass

    assert asset1.op.description == "parameter"


def test_invoking_simple_assets():
    @dg.asset
    def no_input_asset():
        return [1, 2, 3]

    out = no_input_asset()
    assert out == [1, 2, 3]

    @dg.asset
    def arg_input_asset(arg1, arg2):
        return arg1 + arg2

    out = arg_input_asset([1, 2, 3], [4, 5, 6])
    assert out == [1, 2, 3, 4, 5, 6]

    @dg.asset
    def arg_kwarg_asset(arg1, kwarg1=None):
        kwarg1 = kwarg1 or [0]
        return arg1 + kwarg1

    out = arg_kwarg_asset([1, 2, 3], kwarg1=[3, 2, 1])
    assert out == [1, 2, 3, 3, 2, 1]

    out = arg_kwarg_asset([1, 2, 3])
    assert out == [1, 2, 3, 0]


def test_invoking_asset_with_deps():
    @dg.asset
    def upstream():
        return [1]

    @dg.asset
    def downstream(upstream):
        return upstream + [2, 3]

    # check that the asset dependencies are in place
    assert dg.materialize([upstream, downstream]).success

    out = downstream([3])
    assert out == [3, 2, 3]


def test_invoking_asset_with_context():
    @dg.asset
    def asset_with_context(context, arg1):
        assert isinstance(context, dg.AssetExecutionContext)
        return arg1

    ctx = dg.build_asset_context()
    out = asset_with_context(ctx, 1)
    assert out == 1


def test_partitions_def():
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])

    @dg.asset(partitions_def=partitions_def)
    def my_asset():
        pass

    assert my_asset.partitions_def == partitions_def


def test_op_tags():
    tags = {"apple": "banana", "orange": {"rind": "fsd", "segment": "fjdskl"}}
    tags_stringified = {"apple": "banana", "orange": '{"rind": "fsd", "segment": "fjdskl"}'}

    @dg.asset(op_tags=tags)
    def my_asset(): ...

    assert my_asset.op.tags == tags_stringified


def test_kwargs():
    @dg.asset(ins={"upstream": dg.AssetIn()})
    def my_asset(**kwargs):
        del kwargs
        return 7

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(upstream=5) == 7
    assert my_asset.op(upstream=5) == 7


def test_kwargs_with_context():
    @dg.asset(ins={"upstream": dg.AssetIn()})
    def my_asset(context, **kwargs):
        assert context
        del kwargs
        return 7

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(dg.build_asset_context(), upstream=5) == 7
    assert my_asset.op(dg.build_op_context(), upstream=5) == 7

    @dg.asset
    def upstream(): ...

    assert dg.materialize_to_memory([upstream, my_asset]).success


def test_kwargs_multi_asset():
    @dg.multi_asset(ins={"upstream": dg.AssetIn()}, outs={"a": dg.AssetOut()})
    def my_asset(**kwargs):
        del kwargs
        return (7,)

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(upstream=5) == (7,)
    assert my_asset.op(upstream=5) == (7,)

    @dg.asset
    def upstream(): ...

    assert dg.materialize_to_memory([upstream, my_asset]).success


def test_kwargs_multi_asset_with_context():
    @dg.multi_asset(ins={"upstream": dg.AssetIn()}, outs={"a": dg.AssetOut()})
    def my_asset(context, **kwargs):
        assert context
        del kwargs
        return (7,)

    assert isinstance(my_asset, dg.AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert dg.AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(dg.build_asset_context(), upstream=5) == (7,)
    assert my_asset.op(dg.build_op_context(), upstream=5) == (7,)

    @dg.asset
    def upstream(): ...

    assert dg.materialize_to_memory([upstream, my_asset]).success


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_multi_asset_resource_defs():
    @dg.resource
    def baz_resource():
        pass

    @dg.io_manager(required_resource_keys={"baz"})  # pyright: ignore[reportArgumentType]
    def foo_manager():
        pass

    @dg.io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    def bar_manager():
        pass

    @dg.multi_asset(
        outs={
            "key1": dg.AssetOut(key=dg.AssetKey("key1"), io_manager_key="foo"),
            "key2": dg.AssetOut(key=dg.AssetKey("key2"), io_manager_key="bar"),
        },
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"foo", "bar", "baz"}

    ensure_requirements_satisfied(
        my_asset.resource_defs, list(my_asset.get_resource_requirements())
    )


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_multi_asset_resource_defs_specs() -> None:
    @dg.resource
    def baz_resource():
        pass

    @dg.io_manager(required_resource_keys={"baz"})  # pyright: ignore[reportArgumentType]
    def foo_manager():
        pass

    @dg.io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    def bar_manager():
        pass

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("key1", metadata={SYSTEM_METADATA_KEY_IO_MANAGER_KEY: "foo"}),
            dg.AssetSpec("key2", metadata={SYSTEM_METADATA_KEY_IO_MANAGER_KEY: "bar"}),
        ],
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"foo", "bar", "baz"}

    ensure_requirements_satisfied(
        my_asset.resource_defs, list(my_asset.get_resource_requirements())
    )


def test_multi_asset_code_versions():
    @dg.multi_asset(
        outs={
            "key1": dg.AssetOut(key=dg.AssetKey("key1"), code_version="foo"),
            "key2": dg.AssetOut(key=dg.AssetKey("key2"), code_version="bar"),
        },
    )
    def my_asset():
        pass

    assert my_asset.code_versions_by_key == {
        dg.AssetKey("key1"): "foo",
        dg.AssetKey("key2"): "bar",
    }


@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_asset_io_manager_def():
    @dg.io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    def the_manager():
        pass

    @dg.asset(io_manager_def=the_manager)
    def the_asset():
        pass

    # If IO manager def is passed directly, then it doesn't appear as a
    # required resource key on the underlying op.
    assert set(the_asset.node_def.required_resource_keys) == set()  # pyright: ignore[reportAttributeAccessIssue]

    @dg.asset(io_manager_key="blah", resource_defs={"blah": the_manager})
    def other_asset():
        pass

    # If IO manager def is provided as a resource def, it appears in required
    # resource keys on the underlying op.
    assert set(other_asset.node_def.required_resource_keys) == {"blah"}  # pyright: ignore[reportAttributeAccessIssue]


def test_asset_retry_policy():
    retry_policy = dg.RetryPolicy()

    @dg.asset(retry_policy=retry_policy)
    def my_asset(): ...

    assert my_asset.op.retry_policy == retry_policy


def test_multi_asset_retry_policy():
    retry_policy = dg.RetryPolicy()

    @dg.multi_asset(
        outs={
            "key1": dg.AssetOut(key=dg.AssetKey("key1")),
            "key2": dg.AssetOut(key=dg.AssetKey("key2")),
        },
        retry_policy=retry_policy,
    )
    def my_asset(): ...

    assert my_asset.op.retry_policy == retry_policy


@pytest.mark.parametrize(
    "partitions_def,partition_mapping",
    [
        (None, None),
        (dg.DailyPartitionsDefinition(start_date="2020-01-01"), dg.TimeWindowPartitionMapping()),
        (
            dg.DailyPartitionsDefinition(start_date="2020-01-01"),
            dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=0),
        ),
        (
            dg.MultiPartitionsDefinition(
                {
                    "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
                    "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            None,
        ),
        (
            dg.MultiPartitionsDefinition(
                {
                    "time": dg.DailyPartitionsDefinition(start_date="2020-01-01"),
                    "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            dg.MultiPartitionMapping({}),
        ),
        (
            dg.MultiPartitionsDefinition(
                {
                    "time": dg.DailyPartitionsDefinition(start_date="2020-01-01"),
                    "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            dg.MultiPartitionMapping(
                {
                    "time": dg.DimensionPartitionMapping(
                        "time", dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=0)
                    ),
                    "abc": dg.DimensionPartitionMapping("abc", dg.IdentityPartitionMapping()),
                }
            ),
        ),
    ],
)
def test_invalid_self_dep(partitions_def, partition_mapping):
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Assets can only depend on themselves if"
    ):

        @dg.asset(
            partitions_def=partitions_def,
            ins={"b": dg.AssetIn(partition_mapping=partition_mapping)},
        )
        def b(b):
            del b


@ignore_warning("Class `MultiPartitionMapping` is currently in beta")
def test_invalid_self_dep_no_time_dimension():
    partitions_def = dg.MultiPartitionsDefinition(
        {
            "123": dg.StaticPartitionsDefinition(["1", "2", "3"]),
            "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )
    partition_mapping = dg.MultiPartitionMapping(
        {
            "123": dg.DimensionPartitionMapping("123", dg.IdentityPartitionMapping()),
            "abc": dg.DimensionPartitionMapping("abc", dg.IdentityPartitionMapping()),
        }
    )
    with pytest.raises(CheckError, match="Expected exactly one time window partitioned dimension"):

        @dg.asset(
            partitions_def=partitions_def,
            ins={"b": dg.AssetIn(partition_mapping=partition_mapping)},
        )
        def b(b):
            del b


def test_asset_in_nothing() -> None:
    @dg.asset(ins={"upstream": dg.AssetIn(dagster_type=Nothing)})
    def asset1(): ...

    assert dg.AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert dg.materialize_to_memory([asset1]).success


def test_asset_in_nothing_and_something():
    @dg.asset
    def other_upstream(): ...

    @dg.asset(ins={"upstream": dg.AssetIn(dagster_type=Nothing)})
    def asset1(other_upstream):
        del other_upstream

    assert dg.AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert dg.AssetKey("other_upstream") in asset1.keys_by_input_name.values()
    assert dg.materialize_to_memory([other_upstream, asset1]).success


def test_asset_in_nothing_context():
    @dg.asset(ins={"upstream": dg.AssetIn(dagster_type=Nothing)})
    def asset1(context):
        del context

    assert dg.AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert dg.materialize_to_memory([asset1]).success


def test_graph_asset_decorator_no_args():
    @dg.op
    def my_op(x, y):
        del y
        return x

    @dg.graph_asset
    def my_graph(x, y):
        return my_op(x, y)

    assert my_graph.keys_by_input_name["x"] == dg.AssetKey("x")
    assert my_graph.keys_by_input_name["y"] == dg.AssetKey("y")
    assert my_graph.keys_by_output_name["result"] == dg.AssetKey("my_graph")


@ignore_warning("Class `FreshnessPolicy` is deprecated")
@ignore_warning("Class `AutoMaterializePolicy` is currently in beta")
@ignore_warning("Class `MaterializeOnRequiredForFreshnessRule` is deprecated")
@ignore_warning("Function `AutoMaterializePolicy.lazy` is deprecated")
@ignore_warning("Static method `AutomationCondition.eager` is currently in beta")
@ignore_warning("Parameter `auto_materialize_policy` is deprecated")
@ignore_warning("Parameter `resource_defs` .* is currently in beta")
@ignore_warning("Parameter `tags` .* is currently in beta")
@ignore_warning("Parameter `owners` .* is currently in beta")
@ignore_warning("Parameter `auto_materialize_policy` .* is deprecated")
@ignore_warning("Parameter `freshness_policy` .* is deprecated")
@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
@ignore_warning("Parameter `legacy_freshness_policy`")
@ignore_warning("Class `LegacyFreshnessPolicy`")
@pytest.mark.parametrize(
    "automation_condition_arg",
    [
        {"auto_materialize_policy": AutomationCondition.eager().as_auto_materialize_policy()},
        {"automation_condition": AutomationCondition.eager()},
    ],
)
def test_graph_asset_with_args(automation_condition_arg):
    @dg.resource
    def foo_resource():
        pass

    @dg.op
    def my_op1(x):
        return x

    @dg.op
    def my_op2(y):
        return y

    @dg.graph_asset(
        group_name="group1",
        metadata={"my_metadata": "some_metadata"},
        legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=5),
        resource_defs={"foo": foo_resource},
        tags={"foo": "bar"},
        owners=["team:team1", "claire@dagsterlabs.com"],
        code_version="v1",
        **automation_condition_arg,
    )
    def my_asset(x):
        return my_op2(my_op1(x))

    assert my_asset.group_names_by_key[dg.AssetKey("my_asset")] == "group1"
    assert my_asset.metadata_by_key[dg.AssetKey("my_asset")] == {"my_metadata": "some_metadata"}
    assert my_asset.legacy_freshness_policies_by_key[
        dg.AssetKey("my_asset")
    ] == dg.LegacyFreshnessPolicy(maximum_lag_minutes=5)
    assert my_asset.tags_by_key[dg.AssetKey("my_asset")] == {"foo": "bar"}
    assert my_asset.specs_by_key[dg.AssetKey("my_asset")].owners == [
        "team:team1",
        "claire@dagsterlabs.com",
    ]
    assert (
        my_asset.automation_conditions_by_key[dg.AssetKey("my_asset")]
        == AutomationCondition.eager()
    )
    assert my_asset.resource_defs["foo"] == foo_resource
    assert my_asset.code_versions_by_key[dg.AssetKey("my_asset")] == "v1"


def test_graph_asset_partitioned():
    @dg.op
    def my_op(context):
        assert context.partition_key == "a"

    @dg.graph_asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
    def my_asset():
        return my_op()

    assert dg.materialize_to_memory([my_asset], partition_key="a").success


def test_graph_asset_partition_mapping():
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c"])

    @dg.asset(partitions_def=partitions_def)
    def asset1(): ...

    @dg.op(ins={"in1": dg.In(dg.Nothing)})
    def my_op(context):
        assert context.partition_key == "a"
        assert context.asset_partition_keys_for_input("in1") == ["a", "b", "c"]

    @dg.graph_asset(
        partitions_def=partitions_def,
        ins={"asset1": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())},
    )
    def my_asset(asset1):
        return my_op(asset1)

    assert my_asset.get_partition_mapping(dg.AssetKey("asset1")) == dg.AllPartitionMapping()

    assert dg.materialize_to_memory([asset1, my_asset], partition_key="a").success


@ignore_warning("Parameter `kinds` of function")
def test_graph_asset_kinds() -> None:
    @dg.asset()
    def asset1(): ...

    @dg.op(ins={"in1": dg.In(dg.Nothing)})
    def my_op(context) -> None:
        pass

    @dg.graph_asset(ins={"asset1": dg.AssetIn()}, kinds={"python"})
    def my_graph_asset(asset1) -> None:
        return my_op(asset1)

    assert dg.materialize_to_memory([asset1, my_graph_asset]).success

    assert my_graph_asset.specs_by_key[dg.AssetKey("my_graph_asset")].kinds == {"python"}
    assert my_graph_asset.tags_by_key[dg.AssetKey("my_graph_asset")] == build_kind_tag("python")

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match=r"Assets can have at most ten kinds currently."
    ):
        kinds = {f"kind_{i}" for i in range(11)}

        @dg.graph_asset(kinds=kinds)
        def assets2(): ...


def test_graph_asset_w_key_prefix():
    @dg.op
    def foo():
        return 1

    @dg.op
    def bar(i):
        return i + 1

    @dg.graph_asset(key_prefix=["this", "is", "a", "prefix"], group_name="abc")
    def the_asset():
        return bar(foo())

    assert the_asset.keys_by_output_name["result"].path == [
        "this",
        "is",
        "a",
        "prefix",
        "the_asset",
    ]

    assert the_asset.group_names_by_key == {
        dg.AssetKey(["this", "is", "a", "prefix", "the_asset"]): "abc"
    }

    @dg.graph_asset(key_prefix="prefix", group_name="abc")
    def str_prefix():
        return bar(foo())

    assert str_prefix.keys_by_output_name["result"].path == ["prefix", "str_prefix"]


@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_graph_asset_w_config_dict():
    class FooConfig(dg.Config):
        val: int

    @dg.op
    def foo_op(config: FooConfig):
        return config.val

    @dg.graph_asset(config={"foo_op": {"config": {"val": 1}}})
    def foo():
        return foo_op()

    result = dg.materialize_to_memory([foo])
    assert result.success
    assert result.output_for_node("foo") == 1

    @dg.graph_multi_asset(
        outs={"first_asset": dg.AssetOut()},
        config={"foo_op": {"config": {"val": 1}}},
    )
    def bar():
        x = foo_op()
        return {"first_asset": x}

    result = dg.materialize_to_memory([bar])
    assert result.success
    assert result.output_for_node("bar", "first_asset") == 1


@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_graph_asset_w_config_mapping():
    class FooConfig(dg.Config):
        val: int

    @dg.op
    def foo_op(config: FooConfig):
        return config.val

    @dg.config_mapping(config_schema=int)
    def foo_config_mapping(val: Any) -> Any:
        return {"foo_op": {"config": {"val": val}}}

    @dg.graph_asset(config=foo_config_mapping)
    def foo():
        return foo_op()

    result = dg.materialize_to_memory([foo], run_config={"ops": {"foo": {"config": 1}}})
    assert result.success
    assert result.output_for_node("foo") == 1

    @dg.graph_multi_asset(
        outs={"first_asset": dg.AssetOut()},
        config=foo_config_mapping,
    )
    def bar():
        x = foo_op()
        return {"first_asset": x}

    result = dg.materialize_to_memory([bar], run_config={"ops": {"bar": {"config": 1}}})
    assert result.success
    assert result.output_for_node("bar", "first_asset") == 1


@ignore_warning("Class `FreshnessPolicy` is deprecated")
@ignore_warning("Class `AutoMaterializePolicy` is currently in beta")
@ignore_warning("Static method `AutomationCondition.eager` is currently in beta")
@ignore_warning("Class `MaterializeOnRequiredForFreshnessRule` is deprecated")
@ignore_warning("Function `AutoMaterializePolicy.lazy` is deprecated")
@ignore_warning("Parameter `auto_materialize_policy` is deprecated")
@ignore_warning("Parameter `resource_defs`")
@ignore_warning("Parameter `auto_materialize_policy`")
@ignore_warning("Parameter `freshness_policy`")
@ignore_warning("Class `LegacyFreshnessPolicy`")
@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
@ignore_warning("Parameter `legacy_freshness_policy`")
@pytest.mark.parametrize(
    "automation_condition_arg",
    [
        {"auto_materialize_policy": AutomationCondition.eager().as_auto_materialize_policy()},
        {"automation_condition": AutomationCondition.eager()},
    ],
)
def test_graph_multi_asset_decorator(automation_condition_arg):
    @dg.resource
    def foo_resource():
        pass

    @dg.op(out={"one": dg.Out(), "two": dg.Out()})
    def two_in_two_out(context, in1, in2):
        assert context.asset_key_for_input("in1") == dg.AssetKey("x")
        assert context.asset_key_for_input("in2") == dg.AssetKey("y")
        assert context.asset_key_for_output("one") == dg.AssetKey("first_asset")
        assert context.asset_key_for_output("two") == dg.AssetKey("second_asset")
        return 4, 5

    @dg.graph_multi_asset(
        outs={
            "first_asset": dg.AssetOut(code_version="abc", **automation_condition_arg),
            "second_asset": dg.AssetOut(
                legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=5)
            ),
        },
        group_name="grp",
        resource_defs={"foo": foo_resource},
    )
    def two_assets(x, y):
        one, two = two_in_two_out(x, y)
        return {"first_asset": one, "second_asset": two}

    assert two_assets.keys_by_input_name["x"] == dg.AssetKey("x")
    assert two_assets.keys_by_input_name["y"] == dg.AssetKey("y")
    assert two_assets.keys_by_output_name["first_asset"] == dg.AssetKey("first_asset")
    assert two_assets.keys_by_output_name["second_asset"] == dg.AssetKey("second_asset")

    assert two_assets.group_names_by_key[dg.AssetKey("first_asset")] == "grp"
    assert two_assets.code_versions_by_key[dg.AssetKey("first_asset")] == "abc"
    assert two_assets.group_names_by_key[dg.AssetKey("second_asset")] == "grp"

    assert two_assets.legacy_freshness_policies_by_key.get(dg.AssetKey("first_asset")) is None
    assert two_assets.legacy_freshness_policies_by_key[
        dg.AssetKey("second_asset")
    ] == dg.LegacyFreshnessPolicy(maximum_lag_minutes=5)

    assert (
        two_assets.automation_conditions_by_key[dg.AssetKey("first_asset")]
        == AutomationCondition.eager()
    )
    assert two_assets.automation_conditions_by_key.get(dg.AssetKey("second_asset")) is None

    assert two_assets.resource_defs["foo"] == foo_resource

    @dg.asset
    def x():
        return 1

    @dg.asset
    def y():
        return 1

    assert dg.materialize_to_memory([x, y, two_assets]).success


@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_graph_multi_asset_w_key_prefix():
    @dg.op(out={"one": dg.Out(), "two": dg.Out()})
    def two_in_two_out(context, in1, in2):
        assert context.asset_key_for_input("in1") == dg.AssetKey("x")
        assert context.asset_key_for_input("in2") == dg.AssetKey("y")
        assert context.asset_key_for_output("one") == dg.AssetKey("first_asset")
        assert context.asset_key_for_output("two") == dg.AssetKey("second_asset")
        return 4, 5

    @dg.graph_multi_asset(
        ins={"x": dg.AssetIn(key_prefix=["this", "is", "another", "prefix"])},
        outs={
            "first_asset": dg.AssetOut(key_prefix=["this", "is", "a", "prefix"]),
            "second_asset": dg.AssetOut(),
        },
        group_name="grp",
    )
    def two_assets(x, y):
        one, two = two_in_two_out(x, y)
        return {"first_asset": one, "second_asset": two}

    assert two_assets.keys_by_output_name["first_asset"].path == [
        "this",
        "is",
        "a",
        "prefix",
        "first_asset",
    ]

    assert two_assets.keys_by_input_name["x"].path == [
        "this",
        "is",
        "another",
        "prefix",
        "x",
    ]

    assert two_assets.group_names_by_key == {
        dg.AssetKey(["this", "is", "a", "prefix", "first_asset"]): "grp",
        dg.AssetKey(["second_asset"]): "grp",
    }


@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_graph_asset_w_ins_and_param_args():
    @dg.asset
    def upstream():
        return 1

    @dg.op
    def plus_1(x):
        return x + 1

    @dg.graph_asset(ins={"one": dg.AssetIn("upstream")})
    def foo(one):
        return plus_1(one)

    result = dg.materialize_to_memory([upstream, foo])
    assert result.success
    assert result.output_for_node("foo") == 2

    @dg.graph_multi_asset(outs={"first_asset": dg.AssetOut()}, ins={"one": dg.AssetIn("upstream")})
    def bar(one):
        x = plus_1(one)
        return {"first_asset": x}

    result = dg.materialize_to_memory([upstream, bar])
    assert result.success
    assert result.output_for_node("bar", "first_asset") == 2


@ignore_warning("Parameter `tags` of initializer `AssetOut.__init__` is currently in beta")
@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_multi_asset_graph_asset_w_tags():
    @dg.op
    def return_1():
        return 1

    @dg.op
    def plus_1(x):
        return x + 1

    @dg.graph_multi_asset(
        outs={
            "first_asset": dg.AssetOut(tags={"first": "one"}),
            "second_asset": dg.AssetOut(tags={"second": "two"}),
            "no_tags": dg.AssetOut(),
        }
    )
    def the_asset():
        one = return_1()
        two = plus_1(one)
        three = plus_1(two)
        return {"first_asset": one, "second_asset": two, "no_tags": three}

    result = dg.materialize_to_memory([the_asset])
    assert result.success
    assert the_asset.tags_by_key[dg.AssetKey("first_asset")] == {"first": "one"}
    assert the_asset.tags_by_key[dg.AssetKey("second_asset")] == {"second": "two"}
    assert the_asset.tags_by_key[dg.AssetKey("no_tags")] == {}


@ignore_warning("Parameter `owners` of initializer `AssetOut.__init__` is currently in beta")
@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_multi_asset_graph_asset_w_owners():
    @dg.op
    def return_1():
        return 1

    @dg.op
    def plus_1(x):
        return x + 1

    @dg.graph_multi_asset(
        outs={
            "first_asset": dg.AssetOut(owners=["team:team_name1"]),
            "second_asset": dg.AssetOut(owners=["team:team_name2"]),
            "no_owner": dg.AssetOut(),
        }
    )
    def the_asset():
        one = return_1()
        two = plus_1(one)
        three = plus_1(two)
        return {"first_asset": one, "second_asset": two, "no_owner": three}

    result = dg.materialize_to_memory([the_asset])
    assert result.success
    assert the_asset.owners_by_key[dg.AssetKey("first_asset")] == ["team:team_name1"]
    assert the_asset.owners_by_key[dg.AssetKey("second_asset")] == ["team:team_name2"]
    assert the_asset.owners_by_key[dg.AssetKey("no_owner")] == []


@ignore_warning("Parameter `legacy_freshness_policies_by_output_name`")
def test_graph_asset_w_ins_and_kwargs():
    @dg.asset
    def upstream():
        return 1

    @dg.asset
    def another_upstream():
        return 2

    def concat_op_factory(**kwargs):
        ins = {i: dg.In() for i in kwargs}

        @dg.op(ins=ins)
        def concat_op(**kwargs):
            return list(kwargs.values())

        return concat_op

    @dg.graph_asset(ins={"one": dg.AssetIn("upstream"), "two": dg.AssetIn("another_upstream")})
    def foo_kwargs(**kwargs):
        return concat_op_factory(**kwargs)(**kwargs)

    result = dg.materialize_to_memory([upstream, another_upstream, foo_kwargs])
    assert result.success
    assert result.output_for_node("foo_kwargs") == [1, 2]

    @dg.graph_multi_asset(
        outs={"first_asset": dg.AssetOut()},
        ins={"one": dg.AssetIn("upstream"), "two": dg.AssetIn("another_upstream")},
    )
    def bar_kwargs(**kwargs):
        x = concat_op_factory(**kwargs)(**kwargs)
        return {"first_asset": x}

    result = dg.materialize_to_memory([upstream, another_upstream, bar_kwargs])
    assert result.success
    assert result.output_for_node("bar_kwargs", "first_asset") == [1, 2]


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_multi_asset_with_bare_resource():
    class BareResourceObject:
        pass

    executed = {}

    @dg.multi_asset(
        outs={"o1": dg.AssetOut()}, resource_defs={"bare_resource": BareResourceObject()}
    )
    def my_asset(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    dg.materialize_to_memory([my_asset])

    assert executed["yes"]


@ignore_warning("Class `AutoMaterializePolicy` is currently in beta")
@ignore_warning("Class `MaterializeOnRequiredForFreshnessRule` is currently in beta")
@ignore_warning("Static method `AutomationCondition.on_cron` is currently in beta")
@ignore_warning("Static method `AutomationCondition.eager` is currently in beta")
@ignore_warning("Function `AutoMaterializePolicy.lazy` is deprecated")
@ignore_warning("Parameter `auto_materialize_policy`")
def test_multi_asset_with_automation_conditions():
    ac2 = AutomationCondition.on_cron("@daily")
    ac3 = AutomationCondition.eager()

    @dg.multi_asset(
        outs={
            "o1": dg.AssetOut(),
            "o2": dg.AssetOut(automation_condition=ac2),
            "o3": dg.AssetOut(auto_materialize_policy=ac3.as_auto_materialize_policy()),
        }
    )
    def my_asset(): ...

    assert my_asset.automation_conditions_by_key == {dg.AssetKey("o2"): ac2, dg.AssetKey("o3"): ac3}


@pytest.mark.parametrize(
    "key,expected_key",
    [
        (
            dg.AssetKey(["this", "is", "a", "prefix", "the_asset"]),
            dg.AssetKey(["this", "is", "a", "prefix", "the_asset"]),
        ),
        ("the_asset", dg.AssetKey(["the_asset"])),
        (["prefix", "the_asset"], dg.AssetKey(["prefix", "the_asset"])),
        (("prefix", "the_asset"), dg.AssetKey(["prefix", "the_asset"])),
    ],
)
def test_asset_key_provided(key, expected_key):
    @dg.asset(key=key)
    def foo():
        return 1

    assert foo.key == expected_key


def test_error_on_asset_key_provided():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @dg.asset(key="the_asset", key_prefix="foo")
        def one(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @dg.asset(key="the_asset", name="foo")
        def two(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @dg.asset(key="the_asset", name="foo", key_prefix="bar")
        def three(): ...


def test_dynamic_graph_asset_ins():
    @dg.op(ins={"start_after": dg.In(dg.Nothing)})
    def start_job():
        return "x"

    @dg.op
    def wait_until_job_done(x):
        return x

    @dg.asset
    def foo(): ...

    all_assets = [foo]

    @dg.graph_asset(
        ins={asset.key.path[-1]: dg.AssetIn(asset.key) for asset in all_assets},
    )
    def some_graph_asset(**kwargs):
        # block starting job til "all assets" are materialized
        run_id = start_job([v for v in kwargs.values()])
        return wait_until_job_done(run_id)

    assert dg.materialize([some_graph_asset, foo]).success


def test_graph_inputs_error():
    try:

        @dg.graph_asset(ins={"start": dg.AssetIn(dagster_type=Nothing)})
        def _(): ...

    except dg.DagsterInvalidDefinitionError as err:
        assert "'_' decorated function does not have argument(s) 'start'" in str(err)
        # Ensure that dagster type code path doesn't throw since we're using Nothing type.
        assert "except for Ins that have the Nothing dagster_type" not in str(err)

    try:

        @dg.graph(ins={"start": dg.GraphIn()})
        def _(): ...

    except dg.DagsterInvalidDefinitionError as err:
        assert "'_' decorated function does not have argument(s) 'start'" in str(err)
        # Ensure that dagster type code path doesn't throw since we're using Nothing type.
        assert "except for Ins that have the Nothing dagster_type" not in str(err)
