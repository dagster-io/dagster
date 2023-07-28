import warnings
from typing import Any

import pytest
from dagster import (
    AllPartitionMapping,
    AssetKey,
    AssetOut,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    DimensionPartitionMapping,
    FreshnessPolicy,
    IdentityPartitionMapping,
    In,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    Nothing,
    OpExecutionContext,
    Out,
    Output,
    StaticPartitionsDefinition,
    String,
    TimeWindowPartitionMapping,
    _check as check,
    build_asset_context,
    graph_asset,
    graph_multi_asset,
    io_manager,
    materialize_to_memory,
    op,
    resource,
)
from dagster._check import CheckError
from dagster._core.definitions import (
    AssetIn,
    AssetsDefinition,
    asset,
    build_assets_job,
    multi_asset,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.test_utils import ignore_warning
from dagster._core.types.dagster_type import resolve_dagster_type


@pytest.fixture(autouse=True)
def error_on_warning():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()

    warnings.filterwarnings("error")


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


def test_asset_no_decorator_args_direct_call():
    def func():
        return 1

    my_asset = asset(func)

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_inputs_direct_call():
    def func(arg1):
        return arg1

    my_asset = asset(func)

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("arg1") in my_asset.keys_by_input_name.values()


def test_asset_with_config_schema():
    @asset(config_schema={"foo": int})
    def my_asset(context):
        assert context.op_config["foo"] == 5

    materialize_to_memory([my_asset], run_config={"ops": {"my_asset": {"config": {"foo": 5}}}})

    with pytest.raises(DagsterInvalidConfigError):
        materialize_to_memory([my_asset])


def test_multi_asset_with_config_schema():
    @multi_asset(outs={"o1": AssetOut()}, config_schema={"foo": int})
    def my_asset(context):
        assert context.op_config["foo"] == 5

    materialize_to_memory([my_asset], run_config={"ops": {"my_asset": {"config": {"foo": 5}}}})

    with pytest.raises(DagsterInvalidConfigError):
        materialize_to_memory([my_asset])


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
            "my_out_name": AssetOut(key=AssetKey("my_asset_name")),
            "my_other_out_name": AssetOut(key=AssetKey("my_other_asset")),
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
            "out2": AssetOut(),
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
            "out2": AssetOut(),
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
                "out2": AssetOut(),
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
    def my_asset(my_in_name):
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


@ignore_warning("`version` property on OpDefinition is deprecated")
def test_asset_with_code_version():
    @asset(code_version="foo")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.version == "foo"
    assert my_asset.op.output_def_named("result").code_version == "foo"


@ignore_warning("`version` property on OpDefinition is deprecated")
def test_asset_with_code_version_direct_call():
    def func(arg1):
        return arg1

    my_asset = asset(func, code_version="foo")

    assert my_asset.op.version == "foo"
    assert my_asset.op.output_def_named("result").code_version == "foo"


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


def test_asset_with_inputs_and_key_prefix():
    @asset(key_prefix="my_prefix")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    # this functions differently than the key_prefix arg in this scenario
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


def test_input_key_prefix_str():
    @asset(ins={"arg1": AssetIn(key_prefix="abc")})
    def my_asset(arg1):
        assert arg1

    assert AssetKey(["abc", "arg1"]) in my_asset.keys_by_input_name.values()


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


def test_input_dagster_type():
    my_dagster_type = resolve_dagster_type(str)

    @asset(ins={"arg1": AssetIn(dagster_type=my_dagster_type)})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.ins["arg1"].dagster_type == my_dagster_type


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
    assert my_asset.op.input_defs[0].dagster_type.typing_type == str


def test_infer_output_dagster_type():
    @asset
    def my_asset() -> str:
        return "foo"

    assert my_asset.op.outs["result"].dagster_type.display_name == "String"
    assert my_asset.op.outs["result"].dagster_type.typing_type == str


def test_infer_output_dagster_type_none():
    @asset
    def my_asset() -> None:
        pass

    assert my_asset.op.outs["result"].dagster_type.typing_type == type(None)
    assert my_asset.op.outs["result"].dagster_type.display_name == "Nothing"


def test_infer_output_dagster_type_empty():
    @asset
    def my_asset():
        pass

    assert my_asset.op.outs["result"].dagster_type.typing_type is Any
    assert my_asset.op.outs["result"].dagster_type.display_name == "Any"


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

    ctx = build_asset_context()
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
        return 7

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(upstream=5) == 7
    assert my_asset.op(upstream=5) == 7


def test_kwargs_with_context():
    @asset(ins={"upstream": AssetIn()})
    def my_asset(context, **kwargs):
        assert context
        del kwargs
        return 7

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(build_asset_context(), upstream=5) == 7
    assert my_asset.op(build_asset_context(), upstream=5) == 7

    @asset
    def upstream():
        ...

    assert materialize_to_memory([upstream, my_asset]).success


def test_kwargs_multi_asset():
    @multi_asset(ins={"upstream": AssetIn()}, outs={"a": AssetOut()})
    def my_asset(**kwargs):
        del kwargs
        return (7,)

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(upstream=5) == (7,)
    assert my_asset.op(upstream=5) == (7,)

    @asset
    def upstream():
        ...

    assert materialize_to_memory([upstream, my_asset]).success


def test_kwargs_multi_asset_with_context():
    @multi_asset(ins={"upstream": AssetIn()}, outs={"a": AssetOut()})
    def my_asset(context, **kwargs):
        assert context
        del kwargs
        return (7,)

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert AssetKey("upstream") in my_asset.keys_by_input_name.values()
    assert my_asset(build_asset_context(), upstream=5) == (7,)
    assert my_asset.op(build_asset_context(), upstream=5) == (7,)

    @asset
    def upstream():
        ...

    assert materialize_to_memory([upstream, my_asset]).success


@ignore_warning('"resource_defs" is an experimental argument')
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
            "key1": AssetOut(key=AssetKey("key1"), io_manager_key="foo"),
            "key2": AssetOut(key=AssetKey("key2"), io_manager_key="bar"),
        },
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"foo", "bar", "baz"}

    ensure_requirements_satisfied(
        my_asset.resource_defs, list(my_asset.get_resource_requirements())
    )


def test_multi_asset_code_versions():
    @multi_asset(
        outs={
            "key1": AssetOut(key=AssetKey("key1"), code_version="foo"),
            "key2": AssetOut(key=AssetKey("key2"), code_version="bar"),
        },
    )
    def my_asset():
        pass

    assert my_asset.code_versions_by_key == {
        AssetKey("key1"): "foo",
        AssetKey("key2"): "bar",
    }


@ignore_warning('"io_manager_def" is an experimental argument')
@ignore_warning('"resource_defs" is an experimental argument')
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


def test_asset_retry_policy():
    retry_policy = RetryPolicy()

    @asset(retry_policy=retry_policy)
    def my_asset():
        ...

    assert my_asset.op.retry_policy == retry_policy


def test_multi_asset_retry_policy():
    retry_policy = RetryPolicy()

    @multi_asset(
        outs={
            "key1": AssetOut(key=AssetKey("key1")),
            "key2": AssetOut(key=AssetKey("key2")),
        },
        retry_policy=retry_policy,
    )
    def my_asset():
        ...

    assert my_asset.op.retry_policy == retry_policy


@pytest.mark.parametrize(
    "partitions_def,partition_mapping",
    [
        (None, None),
        (DailyPartitionsDefinition(start_date="2020-01-01"), TimeWindowPartitionMapping()),
        (
            DailyPartitionsDefinition(start_date="2020-01-01"),
            TimeWindowPartitionMapping(start_offset=-1, end_offset=0),
        ),
        (
            MultiPartitionsDefinition(
                {
                    "123": StaticPartitionsDefinition(["1", "2", "3"]),
                    "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            None,
        ),
        (
            MultiPartitionsDefinition(
                {
                    "time": DailyPartitionsDefinition(start_date="2020-01-01"),
                    "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            MultiPartitionMapping({}),
        ),
        (
            MultiPartitionsDefinition(
                {
                    "time": DailyPartitionsDefinition(start_date="2020-01-01"),
                    "abc": StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            MultiPartitionMapping(
                {
                    "time": DimensionPartitionMapping(
                        "time", TimeWindowPartitionMapping(start_offset=-1, end_offset=0)
                    ),
                    "abc": DimensionPartitionMapping("abc", IdentityPartitionMapping()),
                }
            ),
        ),
    ],
)
def test_invalid_self_dep(partitions_def, partition_mapping):
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Assets can only depend on themselves if"
    ):

        @asset(
            partitions_def=partitions_def,
            ins={"b": AssetIn(partition_mapping=partition_mapping)},
        )
        def b(b):
            del b


@ignore_warning('"MultiPartitionMapping" is an experimental class')
def test_invalid_self_dep_no_time_dimension():
    partitions_def = MultiPartitionsDefinition(
        {
            "123": StaticPartitionsDefinition(["1", "2", "3"]),
            "abc": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )
    partition_mapping = MultiPartitionMapping(
        {
            "123": DimensionPartitionMapping("123", IdentityPartitionMapping()),
            "abc": DimensionPartitionMapping("abc", IdentityPartitionMapping()),
        }
    )
    with pytest.raises(CheckError, match="Expected exactly one time window partitioned dimension"):

        @asset(
            partitions_def=partitions_def,
            ins={"b": AssetIn(partition_mapping=partition_mapping)},
        )
        def b(b):
            del b


def test_asset_in_nothing():
    @asset(ins={"upstream": AssetIn(dagster_type=Nothing)})
    def asset1():
        ...

    assert AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert materialize_to_memory([asset1]).success


def test_asset_in_nothing_and_something():
    @asset
    def other_upstream():
        ...

    @asset(ins={"upstream": AssetIn(dagster_type=Nothing)})
    def asset1(other_upstream):
        del other_upstream

    assert AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert AssetKey("other_upstream") in asset1.keys_by_input_name.values()
    assert materialize_to_memory([other_upstream, asset1]).success


def test_asset_in_nothing_context():
    @asset(ins={"upstream": AssetIn(dagster_type=Nothing)})
    def asset1(context):
        del context

    assert AssetKey("upstream") in asset1.keys_by_input_name.values()
    assert materialize_to_memory([asset1]).success


def test_graph_asset_decorator_no_args():
    @op
    def my_op(x, y):
        del y
        return x

    @graph_asset
    def my_graph(x, y):
        return my_op(x, y)

    assert my_graph.keys_by_input_name["x"] == AssetKey("x")
    assert my_graph.keys_by_input_name["y"] == AssetKey("y")
    assert my_graph.keys_by_output_name["result"] == AssetKey("my_graph")


@ignore_warning('"FreshnessPolicy" is an experimental class')
@ignore_warning('"AutoMaterializePolicy" is an experimental class')
@ignore_warning('"resource_defs" is an experimental argument')
def test_graph_asset_with_args():
    @resource
    def foo_resource():
        pass

    @op
    def my_op1(x):
        return x

    @op
    def my_op2(y):
        return y

    @graph_asset(
        group_name="group1",
        metadata={"my_metadata": "some_metadata"},
        freshness_policy=FreshnessPolicy(maximum_lag_minutes=5),
        auto_materialize_policy=AutoMaterializePolicy.lazy(),
        resource_defs={"foo": foo_resource},
    )
    def my_asset(x):
        return my_op2(my_op1(x))

    assert my_asset.group_names_by_key[AssetKey("my_asset")] == "group1"
    assert my_asset.metadata_by_key[AssetKey("my_asset")] == {"my_metadata": "some_metadata"}
    assert my_asset.freshness_policies_by_key[AssetKey("my_asset")] == FreshnessPolicy(
        maximum_lag_minutes=5
    )
    assert (
        my_asset.auto_materialize_policies_by_key[AssetKey("my_asset")]
        == AutoMaterializePolicy.lazy()
    )
    assert my_asset.resource_defs["foo"] == foo_resource


def test_graph_asset_partitioned():
    @op
    def my_op(context):
        assert context.partition_key == "a"

    @graph_asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
    def my_asset():
        return my_op()

    assert materialize_to_memory([my_asset], partition_key="a").success


def test_graph_asset_partition_mapping():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @op(ins={"in1": In(Nothing)})
    def my_op(context):
        assert context.partition_key == "a"
        assert context.asset_partition_keys_for_input("in1") == ["a"]

    @graph_asset(
        partitions_def=partitions_def,
        ins={"asset1": AssetIn(partition_mapping=AllPartitionMapping())},
    )
    def my_asset(asset1):
        return my_op(asset1)

    assert materialize_to_memory([asset1, my_asset], partition_key="a").success


def test_graph_asset_w_key_prefix():
    @op
    def foo():
        return 1

    @op
    def bar(i):
        return i + 1

    @graph_asset(key_prefix=["this", "is", "a", "prefix"], group_name="abc")
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
        AssetKey(["this", "is", "a", "prefix", "the_asset"]): "abc"
    }

    @graph_asset(key_prefix="prefix", group_name="abc")
    def str_prefix():
        return bar(foo())

    assert str_prefix.keys_by_output_name["result"].path == ["prefix", "str_prefix"]


@ignore_warning('"FreshnessPolicy" is an experimental class')
@ignore_warning('"AutoMaterializePolicy" is an experimental class')
@ignore_warning('"resource_defs" is an experimental argument')
def test_graph_multi_asset_decorator():
    @resource
    def foo_resource():
        pass

    @op(out={"one": Out(), "two": Out()})
    def two_in_two_out(context, in1, in2):
        assert context.asset_key_for_input("in1") == AssetKey("x")
        assert context.asset_key_for_input("in2") == AssetKey("y")
        assert context.asset_key_for_output("one") == AssetKey("first_asset")
        assert context.asset_key_for_output("two") == AssetKey("second_asset")
        return 4, 5

    @graph_multi_asset(
        outs={
            "first_asset": AssetOut(auto_materialize_policy=AutoMaterializePolicy.eager()),
            "second_asset": AssetOut(freshness_policy=FreshnessPolicy(maximum_lag_minutes=5)),
        },
        group_name="grp",
        resource_defs={"foo": foo_resource},
    )
    def two_assets(x, y):
        one, two = two_in_two_out(x, y)
        return {"first_asset": one, "second_asset": two}

    assert two_assets.keys_by_input_name["x"] == AssetKey("x")
    assert two_assets.keys_by_input_name["y"] == AssetKey("y")
    assert two_assets.keys_by_output_name["first_asset"] == AssetKey("first_asset")
    assert two_assets.keys_by_output_name["second_asset"] == AssetKey("second_asset")

    assert two_assets.group_names_by_key[AssetKey("first_asset")] == "grp"
    assert two_assets.group_names_by_key[AssetKey("second_asset")] == "grp"

    assert two_assets.freshness_policies_by_key.get(AssetKey("first_asset")) is None
    assert two_assets.freshness_policies_by_key[AssetKey("second_asset")] == FreshnessPolicy(
        maximum_lag_minutes=5
    )

    assert (
        two_assets.auto_materialize_policies_by_key[AssetKey("first_asset")]
        == AutoMaterializePolicy.eager()
    )
    assert two_assets.auto_materialize_policies_by_key.get(AssetKey("second_asset")) is None

    assert two_assets.resource_defs["foo"] == foo_resource

    @asset
    def x():
        return 1

    @asset
    def y():
        return 1

    assert materialize_to_memory([x, y, two_assets]).success


def test_graph_multi_asset_w_key_prefix():
    @op(out={"one": Out(), "two": Out()})
    def two_in_two_out(context, in1, in2):
        assert context.asset_key_for_input("in1") == AssetKey("x")
        assert context.asset_key_for_input("in2") == AssetKey("y")
        assert context.asset_key_for_output("one") == AssetKey("first_asset")
        assert context.asset_key_for_output("two") == AssetKey("second_asset")
        return 4, 5

    @graph_multi_asset(
        ins={"x": AssetIn(key_prefix=["this", "is", "another", "prefix"])},
        outs={
            "first_asset": AssetOut(key_prefix=["this", "is", "a", "prefix"]),
            "second_asset": AssetOut(),
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
        AssetKey(["this", "is", "a", "prefix", "first_asset"]): "grp",
        AssetKey(["second_asset"]): "grp",
    }


@ignore_warning('"resource_defs" is an experimental argument')
def test_multi_asset_with_bare_resource():
    class BareResourceObject:
        pass

    executed = {}

    @multi_asset(outs={"o1": AssetOut()}, resource_defs={"bare_resource": BareResourceObject()})
    def my_asset(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    materialize_to_memory([my_asset])

    assert executed["yes"]


@ignore_warning('"AutoMaterializePolicy" is an experimental class')
def test_multi_asset_with_auto_materialize_policy():
    @multi_asset(
        outs={
            "o1": AssetOut(),
            "o2": AssetOut(auto_materialize_policy=AutoMaterializePolicy.eager()),
            "o3": AssetOut(auto_materialize_policy=AutoMaterializePolicy.lazy()),
        }
    )
    def my_asset():
        ...

    assert my_asset.auto_materialize_policies_by_key == {
        AssetKey("o2"): AutoMaterializePolicy.eager(),
        AssetKey("o3"): AutoMaterializePolicy.lazy(),
    }


@pytest.mark.parametrize(
    "key,expected_key",
    [
        (
            AssetKey(["this", "is", "a", "prefix", "the_asset"]),
            AssetKey(["this", "is", "a", "prefix", "the_asset"]),
        ),
        ("the_asset", AssetKey(["the_asset"])),
        (["prefix", "the_asset"], AssetKey(["prefix", "the_asset"])),
        (("prefix", "the_asset"), AssetKey(["prefix", "the_asset"])),
    ],
)
def test_asset_key_provided(key, expected_key):
    @asset(key=key)
    def foo():
        return 1

    assert foo.key == expected_key


def test_error_on_asset_key_provided():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @asset(key="the_asset", key_prefix="foo")
        def one():
            ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @asset(key="the_asset", name="foo")
        def two():
            ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="key argument is provided",
    ):

        @asset(key="the_asset", name="foo", key_prefix="bar")
        def three():
            ...
