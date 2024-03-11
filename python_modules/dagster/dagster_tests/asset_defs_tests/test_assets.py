import ast
import datetime
import tempfile
from typing import Sequence

import pytest
from dagster import (
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterEventType,
    DailyPartitionsDefinition,
    Definitions,
    EventRecordsFilter,
    FreshnessPolicy,
    GraphOut,
    IdentityPartitionMapping,
    IOManager,
    IOManagerDefinition,
    LastPartitionMapping,
    Out,
    Output,
    ResourceDefinition,
    build_asset_context,
    define_asset_job,
    fs_io_manager,
    graph,
    graph_multi_asset,
    io_manager,
    job,
    materialize,
    materialize_to_memory,
    op,
    resource,
    with_resources,
)
from dagster._check import CheckError
from dagster._core.definitions import AssetIn, SourceAsset, asset, multi_asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import TeamAssetOwner, UserAssetOwner
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.decorators.asset_decorator import graph_asset
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidPropertyError,
    DagsterInvariantViolationError,
)
from dagster._core.instance import DagsterInstance
from dagster._core.storage.mem_io_manager import InMemoryIOManager
from dagster._core.test_utils import create_test_asset_job, instance_for_test
from dagster._core.types.dagster_type import Nothing


def test_with_replaced_asset_keys():
    @asset(ins={"input2": AssetIn(key_prefix="something_else")})
    def asset1(input1, input2):
        assert input1
        assert input2

    replaced = asset1.with_attributes(
        output_asset_key_replacements={
            AssetKey(["asset1"]): AssetKey(["prefix1", "asset1_changed"])
        },
        input_asset_key_replacements={
            AssetKey(["something_else", "input2"]): AssetKey(["apple", "banana"])
        },
    )

    assert set(replaced.dependency_keys) == {
        AssetKey("input1"),
        AssetKey(["apple", "banana"]),
    }
    assert replaced.keys == {AssetKey(["prefix1", "asset1_changed"])}

    assert replaced.keys_by_input_name["input1"] == AssetKey("input1")

    assert replaced.keys_by_input_name["input2"] == AssetKey(["apple", "banana"])

    assert replaced.keys_by_output_name["result"] == AssetKey(["prefix1", "asset1_changed"])


@pytest.mark.parametrize(
    "subset,expected_keys,expected_inputs,expected_outputs",
    [
        # there are 5 inputs here, because in addition to in1, in2, and in3, "artificial" inputs are
        # needed for both a and b, as c depends on both and could be executed in a separate step
        # depending on how it is subset. in these cases, the step that contains c will need to
        # have inputs for a and b to connect to.
        ("foo,bar,baz,in1,in2,in3,a,b,c,foo2,bar2,baz2", "a,b,c", 5, 3),
        ("foo,bar,baz", None, 0, 0),
        # see above
        ("in1,a,b,c", "a,b,c", 5, 3),
        # see above
        ("foo,in1,a,b,c,bar", "a,b,c", 5, 3),
        ("foo,in1,in2,in3,a,bar", "a", 2, 1),
        ("foo,in1,in2,a,b,bar", "a,b", 2, 2),
        ("in1,in2,in3,b", "b", 0, 1),
    ],
)
def test_subset_for(subset, expected_keys, expected_inputs, expected_outputs):
    @multi_asset(
        outs={"a": AssetOut(), "b": AssetOut(), "c": AssetOut()},
        internal_asset_deps={
            "a": {AssetKey("in1"), AssetKey("in2")},
            "b": set(),
            "c": {AssetKey("a"), AssetKey("b"), AssetKey("in2"), AssetKey("in3")},
        },
        can_subset=True,
    )
    def abc_(context, in1, in2, in3):
        pass

    subbed = abc_.subset_for(
        {AssetKey(key) for key in subset.split(",")}, selected_asset_check_keys=None
    )

    assert subbed.keys == (
        {AssetKey(key) for key in expected_keys.split(",")} if expected_keys else set()
    )

    assert len(subbed.keys_by_input_name) == expected_inputs
    assert len(subbed.keys_by_output_name) == expected_outputs

    # the asset dependency structure should stay the same
    assert subbed.asset_deps == abc_.asset_deps


def test_retain_group():
    @asset(group_name="foo")
    def bar():
        pass

    replaced = bar.with_attributes(
        output_asset_key_replacements={AssetKey(["bar"]): AssetKey(["baz"])}
    )
    assert replaced.group_names_by_key[AssetKey("baz")] == "foo"


def test_with_replaced_description() -> None:
    @multi_asset(
        outs={
            "foo": AssetOut(description="foo"),
            "bar": AssetOut(description="bar"),
            "baz": AssetOut(description="baz"),
        }
    )
    def abc(): ...

    assert abc.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar",
        AssetKey("baz"): "baz",
    }

    # If there's no replacement description for the asset key, the original description is retained.
    replaced = abc.with_attributes(descriptions_by_key={})
    assert replaced.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar",
        AssetKey("baz"): "baz",
    }

    # Otherwise, use the replaced description.
    replaced = abc.with_attributes(descriptions_by_key={AssetKey(["bar"]): "bar_prime"})
    assert replaced.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar_prime",
        AssetKey("baz"): "baz",
    }

    @op
    def op1(): ...

    @op
    def op2(): ...

    @graph_multi_asset(
        outs={"foo": AssetOut(description="foo"), "bar": AssetOut(description="bar")}
    )
    def abc_graph():
        return {"foo": op1(), "bar": op2()}

    assert abc_graph.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar",
    }

    replaced = abc_graph.with_attributes(descriptions_by_key={})
    assert replaced.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar",
    }

    replaced = abc_graph.with_attributes(descriptions_by_key={AssetKey(["bar"]): "bar_prime"})
    assert replaced.descriptions_by_key == {
        AssetKey("foo"): "foo",
        AssetKey("bar"): "bar_prime",
    }


def test_with_replaced_metadata() -> None:
    @multi_asset(
        outs={
            "foo": AssetOut(metadata={"foo": "foo"}),
            "bar": AssetOut(metadata={"bar": "bar"}),
            "baz": AssetOut(metadata={"baz": "baz"}),
        }
    )
    def abc(): ...

    assert abc.metadata_by_key == {
        AssetKey("foo"): {"foo": "foo"},
        AssetKey("bar"): {"bar": "bar"},
        AssetKey("baz"): {"baz": "baz"},
    }

    # If there's no replacement metadata for the asset key, the original metadata is retained.
    replaced = abc.with_attributes(metadata_by_key={})
    assert replaced.metadata_by_key == {
        AssetKey("foo"): {"foo": "foo"},
        AssetKey("bar"): {"bar": "bar"},
        AssetKey("baz"): {"baz": "baz"},
    }

    # Otherwise, use the replaced description.
    replaced = abc.with_attributes(metadata_by_key={AssetKey(["bar"]): {"bar": "bar_prime"}})
    assert replaced.metadata_by_key == {
        AssetKey("foo"): {"foo": "foo"},
        AssetKey("bar"): {"bar": "bar_prime"},
        AssetKey("baz"): {"baz": "baz"},
    }


def test_retain_freshness_policy():
    fp = FreshnessPolicy(maximum_lag_minutes=24.5)

    @asset(freshness_policy=fp)
    def bar():
        pass

    replaced = bar.with_attributes(
        output_asset_key_replacements={AssetKey(["bar"]): AssetKey(["baz"])}
    )
    assert (
        replaced.freshness_policies_by_key[AssetKey(["baz"])]
        == bar.freshness_policies_by_key[AssetKey(["bar"])]
    )


def test_graph_backed_retain_freshness_policy_and_auto_materialize_policy():
    fpa = FreshnessPolicy(maximum_lag_minutes=24.5)
    fpb = FreshnessPolicy(
        maximum_lag_minutes=30.5, cron_schedule="0 0 * * *", cron_schedule_timezone="US/Eastern"
    )
    ampa = AutoMaterializePolicy.eager()
    ampb = AutoMaterializePolicy.lazy()

    @op
    def foo():
        return 1

    @op
    def bar(inp):
        return inp + 1

    @graph(out={"a": GraphOut(), "b": GraphOut(), "c": GraphOut()})
    def my_graph():
        f = foo()
        return bar(f), bar(f), bar(f)

    my_graph_asset = AssetsDefinition.from_graph(
        my_graph,
        freshness_policies_by_output_name={"a": fpa, "b": fpb},
        auto_materialize_policies_by_output_name={"a": ampa, "b": ampb},
    )

    replaced = my_graph_asset.with_attributes(
        output_asset_key_replacements={
            AssetKey("a"): AssetKey("aa"),
            AssetKey("b"): AssetKey("bb"),
            AssetKey("c"): AssetKey("cc"),
        }
    )
    assert replaced.freshness_policies_by_key[AssetKey("aa")] == fpa
    assert replaced.freshness_policies_by_key[AssetKey("bb")] == fpb
    assert replaced.freshness_policies_by_key.get(AssetKey("cc")) is None

    assert replaced.auto_materialize_policies_by_key[AssetKey("aa")] == ampa
    assert replaced.auto_materialize_policies_by_key[AssetKey("bb")] == ampb
    assert replaced.auto_materialize_policies_by_key.get(AssetKey("cc")) is None


def test_retain_metadata_graph():
    @op
    def foo():
        return 1

    @graph
    def bar():
        return foo()

    md = {"foo": "bar", "baz": 12.5}
    original = AssetsDefinition.from_graph(bar, metadata_by_output_name={"result": md})

    replaced = original.with_attributes(
        output_asset_key_replacements={AssetKey(["bar"]): AssetKey(["baz"])}
    )
    assert (
        replaced.metadata_by_key[AssetKey(["baz"])] == original.metadata_by_key[AssetKey(["bar"])]
    )


def test_retain_group_subset():
    @op(out={"a": Out(), "b": Out()})
    def ma_op():
        return 1

    ma = AssetsDefinition(
        node_def=ma_op,
        keys_by_input_name={},
        keys_by_output_name={"a": AssetKey("a"), "b": AssetKey("b")},
        group_names_by_key={AssetKey("a"): "foo", AssetKey("b"): "bar"},
        can_subset=True,
    )

    subset = ma.subset_for({AssetKey("b")}, selected_asset_check_keys=None)
    assert subset.group_names_by_key[AssetKey("b")] == "bar"


def test_retain_partition_mappings():
    @asset(
        ins={"input_last": AssetIn(["input_last"], partition_mapping=LastPartitionMapping())},
        partitions_def=DailyPartitionsDefinition(datetime.datetime(2022, 1, 1)),
    )
    def bar_(input_last):
        pass

    assert isinstance(bar_.get_partition_mapping(AssetKey(["input_last"])), LastPartitionMapping)

    replaced = bar_.with_attributes(
        input_asset_key_replacements={
            AssetKey(["input_last"]): AssetKey(["input_last2"]),
        }
    )

    assert isinstance(
        replaced.get_partition_mapping(AssetKey(["input_last2"])), LastPartitionMapping
    )


def test_chain_replace_and_subset_for():
    @multi_asset(
        outs={"a": AssetOut(), "b": AssetOut(), "c": AssetOut()},
        internal_asset_deps={
            "a": {AssetKey("in1"), AssetKey("in2")},
            "b": set(),
            "c": {AssetKey("a"), AssetKey("b"), AssetKey("in2"), AssetKey("in3")},
        },
        can_subset=True,
    )
    def abc_(context, in1, in2, in3):
        pass

    replaced_1 = abc_.with_attributes(
        output_asset_key_replacements={AssetKey(["a"]): AssetKey(["foo", "foo_a"])},
        input_asset_key_replacements={AssetKey(["in1"]): AssetKey(["foo", "bar_in1"])},
    )

    assert replaced_1.keys == {AssetKey(["foo", "foo_a"]), AssetKey("b"), AssetKey("c")}
    assert replaced_1.asset_deps == {
        AssetKey(["foo", "foo_a"]): {AssetKey(["foo", "bar_in1"]), AssetKey("in2")},
        AssetKey("b"): set(),
        AssetKey("c"): {
            AssetKey(["foo", "foo_a"]),
            AssetKey("b"),
            AssetKey("in2"),
            AssetKey("in3"),
        },
    }

    subbed_1 = replaced_1.subset_for(
        {AssetKey(["foo", "bar_in1"]), AssetKey("in3"), AssetKey(["foo", "foo_a"]), AssetKey("b")},
        selected_asset_check_keys=None,
    )
    assert subbed_1.keys == {AssetKey(["foo", "foo_a"]), AssetKey("b")}

    replaced_2 = subbed_1.with_attributes(
        output_asset_key_replacements={
            AssetKey(["foo", "foo_a"]): AssetKey(["again", "foo", "foo_a"]),
            AssetKey(["b"]): AssetKey(["something", "bar_b"]),
        },
        input_asset_key_replacements={
            AssetKey(["foo", "bar_in1"]): AssetKey(["again", "foo", "bar_in1"]),
            AssetKey(["in2"]): AssetKey(["foo", "in2"]),
            AssetKey(["in3"]): AssetKey(["foo", "in3"]),
        },
    )
    assert replaced_2.keys == {
        AssetKey(["again", "foo", "foo_a"]),
        AssetKey(["something", "bar_b"]),
    }
    assert replaced_2.asset_deps == {
        AssetKey(["again", "foo", "foo_a"]): {
            AssetKey(["again", "foo", "bar_in1"]),
            AssetKey(["foo", "in2"]),
        },
        AssetKey(["something", "bar_b"]): set(),
        AssetKey("c"): {
            AssetKey(["again", "foo", "foo_a"]),
            AssetKey(["something", "bar_b"]),
            AssetKey(["foo", "in2"]),
            AssetKey(["foo", "in3"]),
        },
    }

    subbed_2 = replaced_2.subset_for(
        {
            AssetKey(["again", "foo", "bar_in1"]),
            AssetKey(["again", "foo", "foo_a"]),
            AssetKey(["c"]),
        },
        selected_asset_check_keys=None,
    )
    assert subbed_2.keys == {AssetKey(["again", "foo", "foo_a"])}


def test_fail_on_subset_for_nonsubsettable():
    @multi_asset(outs={"a": AssetOut(), "b": AssetOut(), "c": AssetOut()})
    def abc_(context, start):
        pass

    with pytest.raises(CheckError, match="can_subset=False"):
        abc_.subset_for({AssetKey("start"), AssetKey("a")}, selected_asset_check_keys=None)


def test_fail_for_non_topological_order():
    @multi_asset(
        outs={
            "a": AssetOut(),
            "b": AssetOut(),
        },
        internal_asset_deps={
            "a": set(),
            "b": {AssetKey("a")},
        },
    )
    def foo():
        yield Output(True, "b")
        yield Output(True, "a")

    with pytest.raises(
        DagsterInvariantViolationError, match='Asset "b" was yielded before its dependency "a"'
    ):
        materialize_to_memory([foo])


def test_from_graph_internal_deps():
    @op
    def foo():
        return 1

    @op
    def bar(x):
        return x + 2

    @graph(out={"a": GraphOut(), "b": GraphOut()})
    def baz():
        x = foo()
        return {"a": x, "b": bar(x)}

    baz_asset = AssetsDefinition.from_graph(
        baz,
        keys_by_output_name={"a": AssetKey(["a"]), "b": AssetKey(["b"])},
        internal_asset_deps={"a": set(), "b": {AssetKey("a")}},
    )
    assert materialize_to_memory([baz_asset])


def test_to_source_assets():
    @asset(metadata={"a": "b"}, io_manager_key="abc", description="blablabla")
    def my_asset(): ...

    assert (
        my_asset.to_source_assets()
        == [my_asset.to_source_asset()]
        == [
            SourceAsset(
                AssetKey(["my_asset"]),
                metadata={"a": "b"},
                io_manager_key="abc",
                description="blablabla",
            )
        ]
    )

    @multi_asset(
        outs={
            "my_out_name": AssetOut(
                key=AssetKey("my_asset_name"),
                metadata={"a": "b"},
                io_manager_key="abc",
                description="blablabla",
            ),
            "my_other_out_name": AssetOut(
                key=AssetKey("my_other_asset"),
                metadata={"c": "d"},
                io_manager_key="def",
                description="ablablabl",
            ),
        }
    )
    def my_multi_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    my_asset_name_source_asset = SourceAsset(
        AssetKey(["my_asset_name"]),
        metadata={"a": "b"},
        io_manager_key="abc",
        description="blablabla",
    )
    my_other_asset_source_asset = SourceAsset(
        AssetKey(["my_other_asset"]),
        metadata={"c": "d"},
        io_manager_key="def",
        description="ablablabl",
    )

    assert my_multi_asset.to_source_assets() == [
        my_asset_name_source_asset,
        my_other_asset_source_asset,
    ]

    assert (
        my_multi_asset.to_source_asset(AssetKey(["my_other_asset"])) == my_other_asset_source_asset
    )
    assert my_multi_asset.to_source_asset("my_other_asset") == my_other_asset_source_asset


def test_coerced_asset_keys():
    @asset(ins={"input1": AssetIn(key=["Asset", "1"])})
    def asset1(input1):
        assert input1


def test_asset_with_io_manager_def():
    events = []

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            events.append(f"entered for {context.step_key}")

        def load_input(self, _context):
            pass

    @io_manager
    def the_io_manager():
        return MyIOManager()

    @asset(io_manager_def=the_io_manager)
    def the_asset():
        pass

    result = materialize([the_asset])
    assert result.success
    assert events == ["entered for the_asset"]


def test_asset_with_io_manager_def_plain_old_python_object_iomanager() -> None:
    events = []

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            events.append(f"entered for {context.step_key}")

        def load_input(self, _context):
            pass

    @asset(io_manager_def=MyIOManager())
    def the_asset():
        pass

    result = materialize([the_asset])
    assert result.success
    assert events == ["entered for the_asset"]


def test_multiple_assets_io_manager_defs():
    io_manager_inst = InMemoryIOManager()
    num_times = [0]

    @io_manager
    def the_io_manager():
        num_times[0] += 1
        return io_manager_inst

    # Under the hood, these io managers are mapped to different asset keys, so
    # we expect the io manager initialization to be called multiple times.
    @asset(io_manager_def=the_io_manager)
    def the_asset():
        return 5

    @asset(io_manager_def=the_io_manager)
    def other_asset():
        return 6

    materialize([the_asset, other_asset])

    assert num_times[0] == 2

    the_asset_key = next(key for key in io_manager_inst.values.keys() if key[1] == "the_asset")
    assert io_manager_inst.values[the_asset_key] == 5

    other_asset_key = next(key for key in io_manager_inst.values.keys() if key[1] == "other_asset")
    assert io_manager_inst.values[other_asset_key] == 6


def test_asset_with_io_manager_key_only():
    io_manager_inst = InMemoryIOManager()

    @io_manager
    def the_io_manager():
        return io_manager_inst

    @asset(io_manager_key="the_key")
    def the_asset():
        return 5

    materialize([the_asset], resources={"the_key": the_io_manager})

    assert next(iter(io_manager_inst.values.values())) == 5


def test_asset_both_io_manager_args_provided():
    @io_manager
    def the_io_manager():
        pass

    with pytest.raises(
        CheckError,
        match=(
            "Both io_manager_key and io_manager_def were provided to `@asset` "
            "decorator. Please provide one or the other."
        ),
    ):

        @asset(io_manager_key="the_key", io_manager_def=the_io_manager)
        def the_asset():
            pass


def test_asset_invocation():
    @asset
    def the_asset():
        return 6

    assert the_asset() == 6


def test_asset_invocation_input():
    @asset
    def input_asset(x):
        return x

    assert input_asset(5) == 5


def test_asset_invocation_resource_overrides():
    @asset(required_resource_keys={"foo", "bar"})
    def asset_reqs_resources(context):
        assert context.resources.foo == "foo_resource"
        assert context.resources.bar == "bar_resource"

    asset_reqs_resources(
        build_asset_context(resources={"foo": "foo_resource", "bar": "bar_resource"})
    )

    @asset(
        resource_defs={
            "foo": ResourceDefinition.hardcoded_resource("orig_foo"),
            "bar": ResourceDefinition.hardcoded_resource("orig_bar"),
        }
    )
    def asset_resource_overrides(context):
        assert context.resources.foo == "override_foo"
        assert context.resources.bar == "orig_bar"

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="resource 'foo' provided on both the definition and invocation context.",
    ):
        asset_resource_overrides(build_asset_context(resources={"foo": "override_foo"}))


def test_asset_invocation_resource_errors():
    @asset(resource_defs={"ignored": ResourceDefinition.hardcoded_resource("not_used")})
    def asset_doesnt_use_resources():
        pass

    asset_doesnt_use_resources()

    @asset(resource_defs={"used": ResourceDefinition.hardcoded_resource("foo")})
    def asset_uses_resources(context):
        assert context.resources.used == "foo"

    asset_uses_resources(build_asset_context())

    @asset(required_resource_keys={"foo"})
    def required_key_not_provided(_):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by op 'required_key_not_provided' was not provided."
        ),
    ):
        required_key_not_provided(build_asset_context())


def test_multi_asset_resources_execution():
    class MyIOManager(IOManager):
        def __init__(self, the_list):
            self._the_list = the_list

        def handle_output(self, _context, obj):
            self._the_list.append(obj)

        def load_input(self, _context):
            pass

    foo_list = []

    @resource
    def baz_resource():
        return "baz"

    @io_manager(required_resource_keys={"baz"})
    def foo_manager(context):
        assert context.resources.baz == "baz"
        return MyIOManager(foo_list)

    bar_list = []

    @io_manager
    def bar_manager():
        return MyIOManager(bar_list)

    @multi_asset(
        outs={
            "key1": AssetOut(key=AssetKey("key1"), io_manager_key="foo"),
            "key2": AssetOut(key=AssetKey("key2"), io_manager_key="bar"),
        },
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset(context):
        # Required io manager keys are available on the context, same behavoir as ops
        assert hasattr(context.resources, "foo")
        assert hasattr(context.resources, "bar")
        yield Output(1, "key1")
        yield Output(2, "key2")

    with instance_for_test() as instance:
        materialize([my_asset], instance=instance)

    assert foo_list == [1]
    assert bar_list == [2]


def test_graph_backed_asset_resources():
    @op(required_resource_keys={"foo"})
    def the_op(context):
        assert context.resources.foo == "value"
        return context.resources.foo

    @graph
    def basic():
        return the_op()

    asset_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("the_asset")},
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("value")},
    )
    result = materialize_to_memory([asset_provided_resources])
    assert result.success
    assert result.output_for_node("basic") == "value"

    asset_not_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("the_asset")},
    )
    result = materialize_to_memory([asset_not_provided_resources], resources={"foo": "value"})
    assert result.success
    assert result.output_for_node("basic") == "value"


def test_graph_backed_asset_io_manager():
    @op(required_resource_keys={"foo"}, out=Out(io_manager_key="the_manager"))
    def the_op(context):
        assert context.resources.foo == "value"
        return context.resources.foo

    @op
    def ingest(x):
        return x

    @graph
    def basic():
        return ingest(the_op())

    events = []

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            events.append(f"entered handle_output for {context.step_key}")

        def load_input(self, context):
            events.append(f"entered handle_input for {context.upstream_output.step_key}")

    asset_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("the_asset")},
        resource_defs={
            "foo": ResourceDefinition.hardcoded_resource("value"),
            "the_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager()),
        },
    )

    with instance_for_test() as instance:
        result = materialize([asset_provided_resources], instance=instance)
        assert result.success
        assert events == [
            "entered handle_output for basic.the_op",
            "entered handle_input for basic.the_op",
        ]


def test_invalid_graph_backed_assets():
    @op
    def a():
        return 1

    @op
    def validate(inp):
        return inp == 1

    @graph
    def foo():
        a_val = a()
        validate(a_val)
        return a_val

    @graph
    def bar():
        return foo()

    @graph
    def baz():
        return a(), bar(), a()

    with pytest.raises(CheckError, match=r"leaf nodes.*validate"):
        AssetsDefinition.from_graph(foo)

    with pytest.raises(CheckError, match=r"leaf nodes.*bar\.validate"):
        AssetsDefinition.from_graph(bar)

    with pytest.raises(CheckError, match=r"leaf nodes.*baz\.bar\.validate"):
        AssetsDefinition.from_graph(baz)


def test_group_name_requirements():
    @asset(group_name="float")  # reserved python keywords allowed
    def good_name():
        return 1

    with pytest.raises(DagsterInvalidDefinitionError, match="not a valid name in Dagster"):

        @asset(group_name="bad*name")  # regex mismatch
        def bad_name():
            return 2

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Empty asset group name was provided, which is not permitted."
            "Set group_name=None to use the default group_name or set non-empty string"
        ),
    ):

        @asset(group_name="")
        def empty_name():
            return 3


def test_from_graph_w_check_specs():
    @op
    def my_op():
        pass

    @graph(out={"my_out": GraphOut()})
    def my_graph():
        return my_op()

    my_asset = AssetsDefinition.from_graph(
        my_graph, check_specs=[AssetCheckSpec("check1", asset="my_out")]
    )

    assert list(my_asset.check_specs) == [AssetCheckSpec("check1", asset=AssetKey(["my_out"]))]


def test_from_graph_w_key_prefix():
    @op
    def foo():
        return 1

    @op
    def bar(i):
        return i + 1

    @graph
    def silly_graph():
        return bar(foo())

    freshness_policy = FreshnessPolicy(maximum_lag_minutes=60)
    description = "This is a description!"
    metadata = {"test_metadata": "This is some metadata"}

    the_asset = AssetsDefinition.from_graph(
        graph_def=silly_graph,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
        freshness_policies_by_output_name={"result": freshness_policy},
        descriptions_by_output_name={"result": description},
        metadata_by_output_name={"result": metadata},
        group_name="abc",
    )
    assert the_asset.keys_by_output_name["result"].path == [
        "this",
        "is",
        "a",
        "prefix",
        "the",
        "asset",
    ]

    assert the_asset.group_names_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): "abc"
    }

    assert the_asset.freshness_policies_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): freshness_policy
    }

    assert the_asset.descriptions_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): description
    }

    assert the_asset.metadata_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): metadata
    }

    str_prefix = AssetsDefinition.from_graph(
        graph_def=silly_graph,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix="prefix",
    )

    assert str_prefix.keys_by_output_name["result"].path == [
        "prefix",
        "the",
        "asset",
    ]


def test_from_op_w_key_prefix():
    @op
    def foo():
        return 1

    freshness_policy = FreshnessPolicy(maximum_lag_minutes=60)
    description = "This is a description!"
    metadata = {"test_metadata": "This is some metadata"}

    the_asset = AssetsDefinition.from_op(
        op_def=foo,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
        freshness_policies_by_output_name={"result": freshness_policy},
        descriptions_by_output_name={"result": description},
        metadata_by_output_name={"result": metadata},
        group_name="abc",
    )

    assert the_asset.keys_by_output_name["result"].path == [
        "this",
        "is",
        "a",
        "prefix",
        "the",
        "asset",
    ]

    assert the_asset.group_names_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): "abc"
    }

    assert the_asset.freshness_policies_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): freshness_policy
    }

    assert the_asset.descriptions_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): description
    }

    assert the_asset.metadata_by_key == {
        AssetKey(["this", "is", "a", "prefix", "the", "asset"]): metadata
    }

    str_prefix = AssetsDefinition.from_op(
        op_def=foo,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix="prefix",
    )

    assert str_prefix.keys_by_output_name["result"].path == [
        "prefix",
        "the",
        "asset",
    ]


def test_from_op_w_configured():
    @op(config_schema={"bar": str})
    def foo():
        return 1

    the_asset = AssetsDefinition.from_op(op_def=foo.configured({"bar": "abc"}, name="foo2"))
    assert the_asset.keys_by_output_name["result"].path == ["foo2"]


def get_step_keys_from_run(instance: DagsterInstance) -> Sequence[str]:
    engine_events = list(
        instance.get_event_records(EventRecordsFilter(DagsterEventType.ENGINE_EVENT))
    )
    metadata = engine_events[0].event_log_entry.get_dagster_event().engine_event_data.metadata
    step_metadata = metadata["step_keys"]
    return ast.literal_eval(step_metadata.value)  # type: ignore


def get_num_events(instance, run_id, event_type):
    events = instance.get_records_for_run(run_id=run_id, of_type=event_type).records
    return len(events)


def test_graph_backed_asset_subset():
    @op()
    def foo():
        return 1

    @op
    def bar(foo):
        return foo

    @graph(out={"one": GraphOut(), "two": GraphOut()})
    def my_graph():
        one = foo()
        return bar.alias("bar_1")(one), bar.alias("bar_2")(one)

    asset_job = define_asset_job("yay").resolve(
        asset_graph=AssetGraph.from_assets(
            [
                AssetsDefinition.from_graph(my_graph, can_subset=True),
            ]
        )
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(instance=instance, asset_selection=[AssetKey("one")])
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            == 1
        )
        assert get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 1
        step_keys = get_step_keys_from_run(instance)
        assert set(step_keys) == set(["my_graph.foo", "my_graph.bar_1"])


def test_graph_backed_asset_partial_output_selection():
    @op(out={"a": Out(), "b": Out()})
    def foo():
        return 1, 2

    @graph(out={"one": GraphOut(), "two": GraphOut()})
    def graph_asset():
        one, two = foo()
        return one, two

    asset_job = define_asset_job("yay").resolve(
        asset_graph=AssetGraph.from_assets(
            [
                AssetsDefinition.from_graph(graph_asset, can_subset=True),
            ]
        ),
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(instance=instance, asset_selection=[AssetKey("one")])
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            == 1
        )
        # This test will yield two materialization events, for assets "one" and "two". This is
        # because the "foo" op will still be executed, even though we only selected "one".
        assert get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 2
        step_keys = get_step_keys_from_run(instance)
        assert set(step_keys) == set(["graph_asset.foo"])


def test_input_subsetting_graph_backed_asset():
    @asset
    def upstream_1():
        return 1

    @asset
    def upstream_2():
        return 1

    @op
    def bar(foo):
        return foo

    @op
    def baz(up_1, up_2):
        return up_1 + up_2

    @graph(out={"one": GraphOut(), "two": GraphOut(), "three": GraphOut()})
    def my_graph(upstream_1, upstream_2):
        return (
            bar.alias("bar_1")(upstream_1),
            bar.alias("bar_2")(upstream_2),
            baz(upstream_1, upstream_2),
        )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        asset_job = define_asset_job("yay").resolve(
            asset_graph=AssetGraph.from_assets(
                with_resources(
                    [
                        upstream_1,
                        upstream_2,
                        AssetsDefinition.from_graph(my_graph, can_subset=True),
                    ],
                    resource_defs={
                        "io_manager": fs_io_manager.configured({"base_dir": tmpdir_path})
                    },
                ),
            )
        )
        with instance_for_test() as instance:
            # test first bar alias
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("one"), AssetKey("upstream_1")],
            )
            assert result.success
            assert (
                get_num_events(
                    instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                == 2
            )
            assert (
                get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 2
            )
            step_keys = get_step_keys_from_run(instance)
            assert set(step_keys) == set(["my_graph.bar_1", "upstream_1"])

        # test second "bar" alias
        with instance_for_test() as instance:
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("two"), AssetKey("upstream_2")],
            )
            assert result.success
            assert (
                get_num_events(
                    instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                == 2
            )
            assert (
                get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 2
            )
            step_keys = get_step_keys_from_run(instance)
            assert set(step_keys) == set(["my_graph.bar_2", "upstream_2"])

        # test "baz" which uses both inputs
        with instance_for_test() as instance:
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("three"), AssetKey("upstream_1"), AssetKey("upstream_2")],
            )
            assert result.success
            assert (
                get_num_events(
                    instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                == 3
            )
            assert (
                get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 3
            )
            step_keys = get_step_keys_from_run(instance)
            assert set(step_keys) == set(["my_graph.baz", "upstream_1", "upstream_2"])


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_2,num_materializations",
    [
        ([AssetKey("asset_one")], {"out_1"}, None, 1),
        ([AssetKey("asset_two")], {"out_2"}, {"add_one_1"}, 1),
        (
            [AssetKey("asset_two"), AssetKey("asset_three")],
            {"out_2"},
            {"add_one_1", "add_one_2"},
            2,
        ),
        (
            [AssetKey("asset_one"), AssetKey("asset_two"), AssetKey("asset_three")],
            {"out_1", "out_2"},
            {"add_one_1", "add_one_2"},
            3,
        ),
    ],
)
def test_graph_backed_asset_subset_context(
    asset_selection, selected_output_names_op_1, selected_output_names_op_2, num_materializations
):
    @op(out={"out_1": Out(is_required=False), "out_2": Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        assert (num_materializations != 3) == context.is_subset
        if "out_1" in context.selected_output_names:
            yield Output(1, output_name="out_1")
        if "out_2" in context.selected_output_names:
            yield Output(1, output_name="out_2")

    @op(out={"add_one_1": Out(is_required=False), "add_one_2": Out(is_required=False)})
    def add_one(context, x):
        assert context.selected_output_names == selected_output_names_op_2
        assert (num_materializations != 3) == context.is_subset
        if "add_one_1" in context.selected_output_names:
            yield Output(x, output_name="add_one_1")
        if "add_one_2" in context.selected_output_names:
            yield Output(x, output_name="add_one_2")

    @graph(out={"asset_one": GraphOut(), "asset_two": GraphOut(), "asset_three": GraphOut()})
    def three():
        out_1, reused_output = op_1()
        out_2, out_3 = add_one(reused_output)
        return {"asset_one": out_1, "asset_two": out_2, "asset_three": out_3}

    job_def = create_test_asset_job([AssetsDefinition.from_graph(three, can_subset=True)])

    with instance_for_test() as instance:
        result = job_def.execute_in_process(asset_selection=asset_selection, instance=instance)
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_3,num_materializations",
    [
        # Because out_1 of op_1 is an input to generate asset_one and is yielded as asset_4,
        # we materialize it even though it is not selected. A log message will indicate that it is
        # an unexpected materialization.
        ([AssetKey("asset_one")], {"out_1"}, None, 2),
        ([AssetKey("asset_two")], {"out_2"}, {"op_3_1"}, 1),
        ([AssetKey("asset_two"), AssetKey("asset_three")], {"out_2"}, {"op_3_1", "op_3_2"}, 2),
        ([AssetKey("asset_four"), AssetKey("asset_three")], {"out_1", "out_2"}, {"op_3_2"}, 2),
        ([AssetKey("asset_one"), AssetKey("asset_four")], {"out_1"}, None, 2),
        (
            [
                AssetKey("asset_one"),
                AssetKey("asset_two"),
                AssetKey("asset_three"),
                AssetKey("asset_four"),
            ],
            {"out_1", "out_2"},
            {"op_3_1", "op_3_2"},
            4,
        ),
    ],
)
def test_graph_backed_asset_subset_context_intermediate_ops(
    asset_selection, selected_output_names_op_1, selected_output_names_op_3, num_materializations
):
    @op(out={"out_1": Out(is_required=False), "out_2": Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        if "out_1" in context.selected_output_names:
            yield Output(1, output_name="out_1")
        if "out_2" in context.selected_output_names:
            yield Output(1, output_name="out_2")

    @op
    def op_2(x):
        return x

    @op(out={"op_3_1": Out(is_required=False), "op_3_2": Out(is_required=False)})
    def op_3(context, x):
        assert context.selected_output_names == selected_output_names_op_3
        if "op_3_1" in context.selected_output_names:
            yield Output(x, output_name="op_3_1")
        if "op_3_2" in context.selected_output_names:
            yield Output(x, output_name="op_3_2")

    @graph(
        out={
            "asset_one": GraphOut(),
            "asset_two": GraphOut(),
            "asset_three": GraphOut(),
            "asset_four": GraphOut(),
        }
    )
    def graph_asset():
        out_1, out_2 = op_1()
        asset_one = op_2(op_2(out_1))
        asset_two, asset_three = op_3(op_2(out_2))
        return {
            "asset_one": asset_one,
            "asset_two": asset_two,
            "asset_three": asset_three,
            "asset_four": out_1,
        }

    asset_job = define_asset_job("yay").resolve(
        asset_graph=AssetGraph.from_assets(
            [AssetsDefinition.from_graph(graph_asset, can_subset=True)],
        )
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(asset_selection=asset_selection, instance=instance)
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_2,num_materializations",
    [
        ([AssetKey("a")], {"op_1_1"}, None, 1),
        ([AssetKey("b")], {"op_1_2"}, None, 1),
        # The following two test cases will also yield a materialization for b because b
        # is required as an input and directly outputted from the graph. A warning is logged.
        ([AssetKey("c")], {"op_1_2"}, {"op_2_1"}, 2),
        ([AssetKey("c"), AssetKey("d")], {"op_1_2"}, {"op_2_1", "op_2_2"}, 3),
        ([AssetKey("b"), AssetKey("d")], {"op_1_2"}, {"op_2_2"}, 2),
    ],
)
def test_nested_graph_subset_context(
    asset_selection, selected_output_names_op_1, selected_output_names_op_2, num_materializations
):
    @op(out={"op_1_1": Out(is_required=False), "op_1_2": Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        if "op_1_1" in context.selected_output_names:
            yield Output(1, output_name="op_1_1")
        if "op_1_2" in context.selected_output_names:
            yield Output(1, output_name="op_1_2")

    @op(out={"op_2_1": Out(is_required=False), "op_2_2": Out(is_required=False)})
    def op_2(context, x):
        assert context.selected_output_names == selected_output_names_op_2
        if "op_2_2" in context.selected_output_names:
            yield Output(x, output_name="op_2_2")
        if "op_2_1" in context.selected_output_names:
            yield Output(x, output_name="op_2_1")

    @graph(out={"a": GraphOut(), "b": GraphOut()})
    def two_outputs_graph():
        a, b = op_1()
        return {"a": a, "b": b}

    @graph(out={"c": GraphOut(), "d": GraphOut()})
    def downstream_graph(b):
        c, d = op_2(b)
        return {"c": c, "d": d}

    @graph(out={"a": GraphOut(), "b": GraphOut(), "c": GraphOut(), "d": GraphOut()})
    def nested_graph():
        a, b = two_outputs_graph()
        c, d = downstream_graph(b)
        return {"a": a, "b": b, "c": c, "d": d}

    asset_job = define_asset_job("yay").resolve(
        asset_graph=AssetGraph.from_assets(
            [AssetsDefinition.from_graph(nested_graph, can_subset=True)],
        )
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(asset_selection=asset_selection, instance=instance)
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


def test_graph_backed_asset_reused():
    @asset
    def upstream():
        return 1

    @op
    def foo(upstream):
        return 1

    @graph
    def graph_asset(upstream):
        return foo(upstream)

    @asset
    def one_downstream(asset_one):
        return asset_one

    @asset
    def duplicate_one_downstream(duplicate_one):
        return duplicate_one

    with tempfile.TemporaryDirectory() as tmpdir_path:
        asset_job = define_asset_job("yay").resolve(
            asset_graph=AssetGraph.from_assets(
                with_resources(
                    [
                        upstream,
                        AssetsDefinition.from_graph(
                            graph_asset,
                            keys_by_output_name={
                                "result": AssetKey("asset_one"),
                            },
                            can_subset=True,
                        ),
                        AssetsDefinition.from_graph(
                            graph_asset,
                            keys_by_output_name={
                                "result": AssetKey("duplicate_one"),
                            },
                            can_subset=True,
                        ),
                        one_downstream,
                        duplicate_one_downstream,
                    ],
                    resource_defs={
                        "io_manager": fs_io_manager.configured({"base_dir": tmpdir_path})
                    },
                ),
            )
        )

        with instance_for_test() as instance:
            asset_job.execute_in_process(instance=instance, asset_selection=[AssetKey("upstream")])
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("asset_one"), AssetKey("one_downstream")],
            )
            assert result.success
            assert (
                get_num_events(
                    instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                == 2
            )
            assert (
                get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 2
            )
            step_keys = get_step_keys_from_run(instance)
            assert set(step_keys) == set(["graph_asset.foo", "one_downstream"])

            # Other graph-backed asset
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("duplicate_one"), AssetKey("duplicate_one_downstream")],
            )
            assert result.success
            assert (
                get_num_events(
                    instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED
                )
                == 2
            )
            assert (
                get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 2
            )
            step_keys = get_step_keys_from_run(instance)
            assert set(step_keys) == set(["graph_asset.foo", "duplicate_one_downstream"])


def test_self_dependency():
    from dagster import PartitionKeyRange, TimeWindowPartitionMapping

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        ins={
            "a": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def a(a):
        del a

    class MyIOManager(IOManager):
        def handle_output(self, context, obj): ...

        def load_input(self, context):
            assert context.asset_key.path[-1] == "a"
            if context.partition_key == "2020-01-01":
                assert context.asset_partition_keys == []
                assert context.has_asset_partitions
            else:
                assert context.partition_key == "2020-01-02"
                assert context.asset_partition_keys == ["2020-01-01"]
                assert context.asset_partition_key == "2020-01-01"
                assert context.asset_partition_key_range == PartitionKeyRange(
                    "2020-01-01", "2020-01-01"
                )
                assert context.has_asset_partitions

    resources = {"io_manager": MyIOManager()}
    materialize([a], partition_key="2020-01-01", resources=resources)
    materialize([a], partition_key="2020-01-02", resources=resources)


def test_context_assets_def():
    @asset
    def a(context):
        assert context.assets_def.keys == {a.key}
        return 1

    @asset
    def b(context, a):
        assert context.assets_def.keys == {b.key}
        return 2

    asset_job = define_asset_job("yay", [a, b]).resolve(
        asset_graph=AssetGraph.from_assets(
            [a, b],
        )
    )

    asset_job.execute_in_process()


def test_invalid_context_assets_def():
    @op
    def my_op(context):
        context.assets_def  # noqa: B018

    @job
    def my_job():
        my_op()

    with pytest.raises(DagsterInvalidPropertyError, match="does not have an assets definition"):
        my_job.execute_in_process()


def test_asset_takes_bare_resource():
    class BareObjectResource:
        pass

    executed = {}

    @asset(resource_defs={"bare_resource": BareObjectResource()})
    def blah(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    defs = Definitions(assets=[blah])
    defs.get_implicit_global_asset_job_def().execute_in_process()
    assert executed["yes"]


def test_asset_key_with_prefix():
    assert AssetKey("foo").with_prefix("prefix") == AssetKey(["prefix", "foo"])
    assert AssetKey("foo").with_prefix(["prefix_one", "prefix_two"]) == AssetKey(
        ["prefix_one", "prefix_two", "foo"]
    )

    with pytest.raises(CheckError):
        AssetKey("foo").with_prefix(1)


def _exec_asset(asset_def, selection=None):
    result = materialize([asset_def], selection=selection)
    assert result.success
    return result.asset_materializations_for_node(asset_def.node_def.name)


def test_multi_asset_return_none():
    #
    # non-optional Nothing
    #
    @multi_asset(
        outs={
            "asset1": AssetOut(dagster_type=Nothing),
            "asset2": AssetOut(dagster_type=Nothing),
        },
    )
    def my_function():
        # ...materialize assets without IO manager
        pass

    # via job
    _exec_asset(my_function)

    # direct invoke
    my_function()

    #
    # optional (fails)
    #
    @multi_asset(
        outs={
            "asset1": AssetOut(dagster_type=Nothing, is_required=False),
            "asset2": AssetOut(dagster_type=Nothing, is_required=False),
        },
        can_subset=True,
    )
    def subset(context: AssetExecutionContext):
        # ...use context.selected_asset_keys materialize subset of assets without IO manager
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        _exec_asset(subset)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        subset(build_asset_context())

    #
    # untyped (fails)
    #
    @multi_asset(
        outs={
            "asset1": AssetOut(),
            "asset2": AssetOut(),
        },
    )
    def untyped():
        # ...materialize assets without IO manager
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        _exec_asset(untyped)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped()


def test_direct_instantiation_invalid_partition_mapping():
    @op
    def my_op():
        return 1

    with pytest.raises(CheckError, match="received a partition mapping"):
        AssetsDefinition(
            keys_by_input_name={},
            keys_by_output_name={"my_output": AssetKey("foo")},
            node_def=my_op,
            partition_mappings={AssetKey("nonexistent_asset"): IdentityPartitionMapping()},
        )


def test_return_materialization():
    #
    # status quo - use add add_output_metadata
    #
    @asset
    def add(context: AssetExecutionContext):
        context.add_output_metadata(
            metadata={"one": 1},
        )

    mats = _exec_asset(add)
    assert len(mats) == 1
    # working with core metadata repr values sucks, ie IntMetadataValue
    assert "one" in mats[0].metadata
    assert mats[0].tags

    #
    # may want to update this pattern to work better...
    #
    @asset
    def logged(context: AssetExecutionContext):
        context.log_event(
            AssetMaterialization(
                asset_key=context.asset_key,
                metadata={"one": 1},
            )
        )

    mats = _exec_asset(logged)
    # ... currently get implicit materialization for output + logged event
    assert len(mats) == 2
    assert "one" in mats[0].metadata
    # assert mats[0].tags # fails
    # assert "one" in mats[1].metadata  # fails
    assert mats[1].tags

    #
    # main exploration
    #
    @asset
    def ret_untyped(context: AssetExecutionContext):
        return MaterializeResult(
            metadata={"one": 1},
        )

    mats = _exec_asset(ret_untyped)
    assert len(mats) == 1, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags

    #
    # key mismatch
    #
    @asset
    def ret_mismatch(context: AssetExecutionContext):
        return MaterializeResult(
            asset_key="random",
            metadata={"one": 1},
        )

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        mats = _exec_asset(ret_mismatch)


def test_multi_asset_no_out():
    #
    # base case
    #
    table_A = AssetSpec("table_A")
    table_B = AssetSpec("table_B")

    @multi_asset(specs=[table_A, table_B])
    def basic():
        pass

    mats = _exec_asset(basic)

    result = basic()
    assert result is None

    #
    # internal deps
    #
    table_C = AssetSpec("table_C", deps=[table_A, table_B])

    @multi_asset(specs=[table_A, table_B, table_C])
    def basic_deps():
        pass

    _exec_asset(basic_deps)
    assert table_A.key in basic_deps.asset_deps[table_C.key]
    assert table_B.key in basic_deps.asset_deps[table_C.key]

    result = basic_deps()
    assert result is None

    #
    # sub-setting
    #
    @multi_asset(
        specs=[table_A, table_B],
        can_subset=True,
    )
    def basic_subset(context: AssetExecutionContext):
        for key in context.selected_asset_keys:
            yield MaterializeResult(asset_key=key)

    mats = _exec_asset(basic_subset, ["table_A"])
    assert table_A.key in {mat.asset_key for mat in mats}
    assert table_B.key not in {mat.asset_key for mat in mats}

    # selected_asset_keys breaks direct invocation
    # basic_subset(build_asset_context())

    #
    # optional
    #
    @multi_asset(
        specs=[table_A, AssetSpec("table_B", skippable=True)],
    )
    def basic_optional(context: AssetExecutionContext):
        yield MaterializeResult(asset_key="table_A")

    mats = _exec_asset(basic_optional)
    assert table_A.key in {mat.asset_key for mat in mats}
    assert table_B.key not in {mat.asset_key for mat in mats}

    basic_optional(build_asset_context())

    #
    # metadata
    #
    @multi_asset(specs=[table_A, table_B])
    def metadata(context: AssetExecutionContext):
        yield MaterializeResult(asset_key="table_A", metadata={"one": 1})
        yield MaterializeResult(asset_key="table_B", metadata={"two": 2})

    mats = _exec_asset(metadata)
    assert len(mats) == 2
    assert mats[0].metadata["one"]
    assert mats[1].metadata["two"]

    # yielded event processing unresolved for assets
    # results = list(metadata(build_asset_context()))
    # assert len(results) == 2


def test_multi_asset_nodes_out_names():
    sales_users = AssetSpec(["sales", "users"])
    marketing_users = AssetSpec(["marketing", "users"])

    @multi_asset(specs=[sales_users, marketing_users])
    def users():
        pass

    assert len(users.op.output_defs) == 2
    assert {out_def.name for out_def in users.op.output_defs} == {"sales_users", "marketing_users"}


def test_asset_spec_deps():
    @asset
    def table_A():
        pass

    table_b = AssetSpec("table_B", deps=[table_A])
    table_c = AssetSpec("table_C", deps=[table_A, table_b])
    table_b_no_dep = AssetSpec("table_B")
    table_c_no_dep = AssetSpec("table_C")

    @multi_asset(specs=[table_b, table_c])
    def deps_in_specs(): ...

    result = materialize([deps_in_specs, table_A])
    assert result.success
    mats = result.get_asset_materialization_events()
    assert len(mats) == 3
    # first event should be A materialization
    assert mats[0].asset_key == table_A.key

    with pytest.raises(DagsterInvalidDefinitionError, match="Can not pass deps and specs"):

        @multi_asset(specs=[table_b_no_dep, table_c_no_dep], deps=["table_A"])
        def no_deps_in_specs(): ...

    @multi_asset(specs=[table_b, table_c])
    def also_input(table_A): ...

    result = materialize([also_input, table_A])
    assert result.success
    mats = result.get_asset_materialization_events()
    assert len(mats) == 3
    # first event should be A materialization
    assert mats[0].asset_key == table_A.key

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="do not have dependencies on the passed AssetSpec",
    ):

        @multi_asset(specs=[table_b, table_c])
        def rogue_input(table_X): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="do not have dependencies on the passed AssetSpec",
    ):

        @multi_asset(specs=[table_b_no_dep, table_c_no_dep])
        def no_spec_deps_but_input(table_A): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="specify deps on the AssetSpecs directly",
    ):

        @multi_asset(
            specs=[table_b_no_dep, table_c_no_dep],
            deps=[table_A],
        )
        def use_deps(): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="specify deps on the AssetSpecs directly",
    ):

        @multi_asset(
            specs=[table_b_no_dep, table_c_no_dep],
            internal_asset_deps={"table_C": {AssetKey("table_B")}},
        )
        def use_internal_deps(): ...


def test_asset_key_on_context():
    @asset
    def test_asset_key_on_context(context: AssetExecutionContext):
        assert context.asset_key == AssetKey(["test_asset_key_on_context"])

    @asset(key_prefix=["a_prefix"])
    def test_asset_key_on_context_with_prefix(context: AssetExecutionContext):
        assert context.asset_key == AssetKey(["a_prefix", "test_asset_key_on_context_with_prefix"])

    materialize([test_asset_key_on_context, test_asset_key_on_context_with_prefix])


def test_multi_asset_asset_key_on_context():
    @multi_asset(
        outs={
            "my_string_asset": AssetOut(),
        }
    )
    def asset_key_context(context: AssetExecutionContext):
        assert context.asset_key == AssetKey(["my_string_asset"])

    materialize([asset_key_context])

    @multi_asset(
        outs={
            "my_string_asset": AssetOut(),
            "my_int_asset": AssetOut(),
        }
    )
    def two_assets_key_context(context: AssetExecutionContext):
        return context.asset_key, 12

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Cannot call `context.asset_key` in a multi_asset with more than one asset",
    ):
        materialize([two_assets_key_context])

    # test with AssetSpecs

    spec1 = AssetSpec(key="spec1")

    @multi_asset(specs=[spec1])
    def asset_key_context_with_specs(context: AssetExecutionContext):
        assert context.asset_key == AssetKey(["spec1"])

    materialize([asset_key_context_with_specs])

    spec2 = AssetSpec(key="spec2")
    spec3 = AssetSpec(key="spec3")

    @multi_asset(specs=[spec2, spec3])
    def asset_key_context_with_two_specs(context: AssetExecutionContext):
        context.log.info(context.asset_key)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Cannot call `context.asset_key` in a multi_asset with more than one asset",
    ):
        materialize([asset_key_context_with_two_specs])


def test_graph_asset_explicit_coercible_key() -> None:
    @op
    def my_op() -> int:
        return 1

    # conversion
    @graph_asset(key="my_graph_asset")
    def _specified_elsewhere() -> int:
        return my_op()

    assert _specified_elsewhere.key == AssetKey(["my_graph_asset"])


def test_graph_asset_explicit_fully_key() -> None:
    @op
    def my_op() -> int:
        return 1

    @graph_asset(key=AssetKey("my_graph_asset"))
    def _specified_elsewhere() -> int:
        return my_op()

    assert _specified_elsewhere.key == AssetKey(["my_graph_asset"])


def test_graph_asset_cannot_use_key_prefix_name_and_key() -> None:
    @op
    def my_op() -> int:
        return 1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(key_prefix="a_prefix", key=AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(name="a_name", key=AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(name="a_name", key_prefix="a_prefix", key=AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter


def test_asset_owners():
    @asset(owners=["team:team1", "claire@dagsterlabs.com"])
    def my_asset():
        pass

    owners = [TeamAssetOwner("team1"), UserAssetOwner("claire@dagsterlabs.com")]
    assert my_asset.owners_by_key == {my_asset.key: owners}
    assert my_asset.with_attributes().owners_by_key == {my_asset.key: owners}  # copies ok

    @asset(owners=["team:team1", "claire@dagsterlabs.com"])
    def my_asset_2():
        pass

    assert my_asset_2.owners_by_key == {my_asset_2.key: owners}

    @asset(owners=[])
    def asset_3():
        pass

    assert asset_3.owners_by_key == {}

    @asset(owners=None)
    def asset_4():
        pass

    assert asset_4.owners_by_key == {}


def test_invalid_asset_owners():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Owner must be an email address or a team name prefixed with 'team:'",
    ):

        @asset(owners=["arbitrary string"])
        def my_asset():
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Owner must be an email address or a team name prefixed with 'team:'",
    ):

        @asset(owners=["notanemail@com"])
        def my_asset_2():
            pass


def test_multi_asset_owners():
    @multi_asset(
        outs={
            "out1": AssetOut(owners=["team:team1", "user@dagsterlabs.com"]),
            "out2": AssetOut(owners=["user2@dagsterlabs.com"]),
        }
    )
    def my_multi_asset():
        pass

    assert my_multi_asset.owners_by_key == {
        AssetKey("out1"): [TeamAssetOwner("team1"), UserAssetOwner("user@dagsterlabs.com")],
        AssetKey("out2"): [UserAssetOwner("user2@dagsterlabs.com")],
    }


def test_replace_asset_keys_for_asset_with_owners():
    @multi_asset(
        outs={
            "out1": AssetOut(owners=["user@dagsterlabs.com"]),
            "out2": AssetOut(owners=["user@dagsterlabs.com"]),
        }
    )
    def my_multi_asset():
        pass

    assert my_multi_asset.owners_by_key == {
        AssetKey("out1"): [UserAssetOwner("user@dagsterlabs.com")],
        AssetKey("out2"): [UserAssetOwner("user@dagsterlabs.com")],
    }

    prefixed_asset = my_multi_asset.with_attributes(
        output_asset_key_replacements={AssetKey(["out1"]): AssetKey(["prefix", "out1"])}
    )
    assert prefixed_asset.owners_by_key == {
        AssetKey(["prefix", "out1"]): [UserAssetOwner("user@dagsterlabs.com")],
        AssetKey("out2"): [UserAssetOwner("user@dagsterlabs.com")],
    }


def test_asset_spec_with_code_versions():
    @multi_asset(specs=[AssetSpec(key="a", code_version="1"), AssetSpec(key="b", code_version="2")])
    def multi_asset_with_versions():
        yield MaterializeResult("a")
        yield MaterializeResult("b")

    assert multi_asset_with_versions.code_versions_by_key == {
        AssetKey(["a"]): "1",
        AssetKey(["b"]): "2",
    }


def test_asset_spec_with_metadata():
    @multi_asset(
        specs=[AssetSpec(key="a", metadata={"foo": "1"}), AssetSpec(key="b", metadata={"bar": "2"})]
    )
    def multi_asset_with_metadata():
        yield MaterializeResult("a")
        yield MaterializeResult("b")

    assert multi_asset_with_metadata.metadata_by_key == {
        AssetKey(["a"]): {"foo": "1"},
        AssetKey(["b"]): {"bar": "2"},
    }


def test_asset_with_tags():
    @asset(tags={"a": "b"})
    def asset1(): ...

    assert asset1.tags_by_key[asset1.key] == {"a": "b"}

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid tag key"):

        @asset(tags={"a%": "b"})  # key has illegal character
        def asset2(): ...


def test_asset_spec_with_tags():
    @multi_asset(specs=[AssetSpec("asset1", tags={"a": "b"})])
    def assets(): ...

    assert assets.tags_by_key[AssetKey("asset1")] == {"a": "b"}

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid tag key"):

        @multi_asset(specs=[AssetSpec("asset1", tags={"a%": "b"})])  # key has illegal character
        def assets(): ...


def test_asset_out_with_tags():
    @multi_asset(outs={"asset1": AssetOut(tags={"a": "b"})})
    def assets(): ...

    assert assets.tags_by_key[AssetKey("asset1")] == {"a": "b"}

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid tag key"):

        @multi_asset(outs={"asset1": AssetOut(tags={"a%": "b"})})  # key has illegal character
        def assets(): ...
