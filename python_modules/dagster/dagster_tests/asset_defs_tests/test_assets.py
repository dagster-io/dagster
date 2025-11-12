import ast
import datetime
import tempfile
from collections.abc import Sequence

import dagster as dg
import pytest
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    BackfillPolicy,
    DagsterEventType,
    HookContext,
    IOManagerDefinition,
    ResourceDefinition,
    _check as check,
    fs_io_manager,
    graph_asset,
    job,
)
from dagster._check import CheckError
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_DAGSTER_TYPE,
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
)
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._core.instance import DagsterInstance
from dagster._core.types.dagster_type import Any, Int, Nothing


def test_with_replaced_asset_keys():
    @dg.asset(ins={"input2": dg.AssetIn(key_prefix="something_else")})
    def asset1(input1, input2):
        assert input1
        assert input2

    replaced = asset1.with_attributes(
        asset_key_replacements={
            dg.AssetKey(["asset1"]): dg.AssetKey(["prefix1", "asset1_changed"]),
            dg.AssetKey(["something_else", "input2"]): dg.AssetKey(["apple", "banana"]),
        },
    )

    assert set(replaced.dependency_keys) == {
        dg.AssetKey("input1"),
        dg.AssetKey(["apple", "banana"]),
    }
    assert replaced.keys == {dg.AssetKey(["prefix1", "asset1_changed"])}

    assert replaced.keys_by_input_name["input1"] == dg.AssetKey("input1")

    assert replaced.keys_by_input_name["input2"] == dg.AssetKey(["apple", "banana"])

    assert replaced.keys_by_output_name["result"] == dg.AssetKey(["prefix1", "asset1_changed"])


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
    @dg.multi_asset(
        outs={"a": dg.AssetOut(), "b": dg.AssetOut(), "c": dg.AssetOut()},
        internal_asset_deps={
            "a": {dg.AssetKey("in1"), dg.AssetKey("in2")},
            "b": set(),
            "c": {dg.AssetKey("a"), dg.AssetKey("b"), dg.AssetKey("in2"), dg.AssetKey("in3")},
        },
        can_subset=True,
    )
    def abc_(context, in1, in2, in3):
        pass

    subbed = abc_.subset_for(
        {dg.AssetKey(key) for key in subset.split(",")}, selected_asset_check_keys=None
    )

    assert subbed.keys == (
        {dg.AssetKey(key) for key in expected_keys.split(",")} if expected_keys else set()
    )

    assert len(subbed.keys_by_input_name) == expected_inputs
    assert len(subbed.keys_by_output_name) == expected_outputs

    # the asset dependency structure should stay the same
    assert subbed.asset_deps == abc_.asset_deps


def test_subset_with_checks():
    @dg.multi_asset(
        outs={"a": dg.AssetOut(), "b": dg.AssetOut(), "c": dg.AssetOut()},
        check_specs=[
            dg.AssetCheckSpec("check1", asset="a"),
            dg.AssetCheckSpec("check2", asset="b"),
        ],
        can_subset=True,
    )
    def abc_(context, in1, in2, in3): ...

    a, b, c = dg.AssetKey("a"), dg.AssetKey("b"), dg.AssetKey("c")
    check1, check2 = dg.AssetCheckKey(a, "check1"), dg.AssetCheckKey(b, "check2")

    subbed = abc_.subset_for({a, b, c}, selected_asset_check_keys={check1, check2})
    assert subbed.check_specs_by_output_name == abc_.check_specs_by_output_name
    assert len(subbed.check_specs_by_output_name) == 2
    assert len(list(subbed.check_specs)) == 2
    assert subbed.node_check_specs_by_output_name == abc_.node_check_specs_by_output_name

    subbed = abc_.subset_for({a, b}, selected_asset_check_keys={check1})
    assert len(subbed.check_specs_by_output_name) == 1
    assert len(list(subbed.check_specs)) == 1
    assert len(subbed.node_check_specs_by_output_name) == 2

    subbed_again = subbed.subset_for({a, b}, selected_asset_check_keys=set())
    assert len(subbed_again.check_specs_by_output_name) == 0
    assert len(list(subbed_again.check_specs)) == 0
    assert len(subbed_again.node_check_specs_by_output_name) == 2


def test_retain_group():
    @dg.asset(group_name="foo")
    def bar():
        pass

    replaced = bar.with_attributes(
        asset_key_replacements={dg.AssetKey(["bar"]): dg.AssetKey(["baz"])}
    )
    assert replaced.specs_by_key[dg.AssetKey("baz")].group_name == "foo"


def test_retain_freshness_policy():
    fp = dg.LegacyFreshnessPolicy(maximum_lag_minutes=24.5)

    @dg.asset(legacy_freshness_policy=fp)
    def bar():
        pass

    replaced = bar.with_attributes(
        asset_key_replacements={dg.AssetKey(["bar"]): dg.AssetKey(["baz"])}
    )
    assert (
        replaced.specs_by_key[dg.AssetKey(["baz"])].legacy_freshness_policy
        == bar.specs_by_key[dg.AssetKey(["bar"])].legacy_freshness_policy
    )


def test_graph_backed_retain_freshness_policy_and_auto_materialize_policy():
    fpa = dg.LegacyFreshnessPolicy(maximum_lag_minutes=24.5)
    fpb = dg.LegacyFreshnessPolicy(
        maximum_lag_minutes=30.5, cron_schedule="0 0 * * *", cron_schedule_timezone="US/Eastern"
    )
    ampa = AutoMaterializePolicy.eager()
    ampb = AutoMaterializePolicy.lazy()

    @dg.op
    def foo():
        return 1

    @dg.op
    def bar(inp):
        return inp + 1

    @dg.graph(out={"a": dg.GraphOut(), "b": dg.GraphOut(), "c": dg.GraphOut()})
    def my_graph():
        f = foo()
        return bar(f), bar(f), bar(f)

    my_graph_asset = AssetsDefinition.from_graph(
        my_graph,
        legacy_freshness_policies_by_output_name={"a": fpa, "b": fpb},
        auto_materialize_policies_by_output_name={"a": ampa, "b": ampb},
    )

    replaced = my_graph_asset.with_attributes(
        asset_key_replacements={
            dg.AssetKey("a"): dg.AssetKey("aa"),
            dg.AssetKey("b"): dg.AssetKey("bb"),
            dg.AssetKey("c"): dg.AssetKey("cc"),
        }
    )
    specs_by_key = replaced.specs_by_key
    assert specs_by_key[dg.AssetKey("aa")].legacy_freshness_policy == fpa
    assert specs_by_key[dg.AssetKey("bb")].legacy_freshness_policy == fpb
    assert specs_by_key[dg.AssetKey("cc")].legacy_freshness_policy is None

    assert specs_by_key[dg.AssetKey("aa")].auto_materialize_policy == ampa
    assert specs_by_key[dg.AssetKey("bb")].auto_materialize_policy == ampb
    assert specs_by_key[dg.AssetKey("cc")].auto_materialize_policy is None


def test_retain_metadata_graph():
    @dg.op
    def foo():
        return 1

    @dg.graph
    def bar():
        return foo()

    md = {"foo": "bar", "baz": 12.5}
    original = AssetsDefinition.from_graph(bar, metadata_by_output_name={"result": md})

    replaced = original.with_attributes(
        asset_key_replacements={dg.AssetKey(["bar"]): dg.AssetKey(["baz"])}
    )
    assert (
        replaced.specs_by_key[dg.AssetKey(["baz"])].metadata
        == original.specs_by_key[dg.AssetKey(["bar"])].metadata
    )


def test_retain_group_subset():
    @dg.op(out={"a": dg.Out(), "b": dg.Out()})
    def ma_op():
        return 1

    ma = dg.AssetsDefinition(
        node_def=ma_op,
        keys_by_input_name={},
        keys_by_output_name={"a": dg.AssetKey("a"), "b": dg.AssetKey("b")},
        group_names_by_key={dg.AssetKey("a"): "foo", dg.AssetKey("b"): "bar"},
        can_subset=True,
    )

    subset = ma.subset_for({dg.AssetKey("b")}, selected_asset_check_keys=None)
    assert subset.specs_by_key[dg.AssetKey("b")].group_name == "bar"


def test_retain_partition_mappings():
    @dg.asset(
        ins={"input_last": dg.AssetIn(["input_last"], partition_mapping=dg.LastPartitionMapping())},
        partitions_def=dg.DailyPartitionsDefinition(datetime.datetime(2022, 1, 1)),
    )
    def bar_(input_last):
        pass

    assert isinstance(
        bar_.get_partition_mapping(dg.AssetKey(["input_last"])), dg.LastPartitionMapping
    )

    replaced = bar_.with_attributes(
        asset_key_replacements={
            dg.AssetKey(["input_last"]): dg.AssetKey(["input_last2"]),
        }
    )

    assert isinstance(
        replaced.get_partition_mapping(dg.AssetKey(["input_last2"])), dg.LastPartitionMapping
    )


def test_chain_replace_and_subset_for():
    @dg.multi_asset(
        outs={"a": dg.AssetOut(), "b": dg.AssetOut(), "c": dg.AssetOut()},
        internal_asset_deps={
            "a": {dg.AssetKey("in1"), dg.AssetKey("in2")},
            "b": set(),
            "c": {dg.AssetKey("a"), dg.AssetKey("b"), dg.AssetKey("in2"), dg.AssetKey("in3")},
        },
        can_subset=True,
    )
    def abc_(context, in1, in2, in3):
        pass

    replaced_1 = abc_.with_attributes(
        asset_key_replacements={
            dg.AssetKey(["a"]): dg.AssetKey(["foo", "foo_a"]),
            dg.AssetKey(["in1"]): dg.AssetKey(["foo", "bar_in1"]),
        },
    )

    assert replaced_1.keys == {dg.AssetKey(["foo", "foo_a"]), dg.AssetKey("b"), dg.AssetKey("c")}
    assert replaced_1.asset_deps == {
        dg.AssetKey(["foo", "foo_a"]): {dg.AssetKey(["foo", "bar_in1"]), dg.AssetKey("in2")},
        dg.AssetKey("b"): set(),
        dg.AssetKey("c"): {
            dg.AssetKey(["foo", "foo_a"]),
            dg.AssetKey("b"),
            dg.AssetKey("in2"),
            dg.AssetKey("in3"),
        },
    }

    subbed_1 = replaced_1.subset_for(
        {
            dg.AssetKey(["foo", "bar_in1"]),
            dg.AssetKey("in3"),
            dg.AssetKey(["foo", "foo_a"]),
            dg.AssetKey("b"),
        },
        selected_asset_check_keys=None,
    )
    assert subbed_1.keys == {dg.AssetKey(["foo", "foo_a"]), dg.AssetKey("b")}

    replaced_2 = subbed_1.with_attributes(
        asset_key_replacements={
            dg.AssetKey(["foo", "foo_a"]): dg.AssetKey(["again", "foo", "foo_a"]),
            dg.AssetKey(["b"]): dg.AssetKey(["something", "bar_b"]),
            dg.AssetKey(["foo", "bar_in1"]): dg.AssetKey(["again", "foo", "bar_in1"]),
            dg.AssetKey(["in2"]): dg.AssetKey(["foo", "in2"]),
            dg.AssetKey(["in3"]): dg.AssetKey(["foo", "in3"]),
        },
    )
    assert replaced_2.keys == {
        dg.AssetKey(["again", "foo", "foo_a"]),
        dg.AssetKey(["something", "bar_b"]),
    }
    assert replaced_2.asset_deps == {
        dg.AssetKey(["again", "foo", "foo_a"]): {
            dg.AssetKey(["again", "foo", "bar_in1"]),
            dg.AssetKey(["foo", "in2"]),
        },
        dg.AssetKey(["something", "bar_b"]): set(),
        dg.AssetKey("c"): {
            dg.AssetKey(["again", "foo", "foo_a"]),
            dg.AssetKey(["something", "bar_b"]),
            dg.AssetKey(["foo", "in2"]),
            dg.AssetKey(["foo", "in3"]),
        },
    }

    subbed_2 = replaced_2.subset_for(
        {
            dg.AssetKey(["again", "foo", "bar_in1"]),
            dg.AssetKey(["again", "foo", "foo_a"]),
            dg.AssetKey(["c"]),
        },
        selected_asset_check_keys=None,
    )
    assert subbed_2.keys == {dg.AssetKey(["again", "foo", "foo_a"])}


def test_fail_on_subset_for_nonsubsettable():
    @dg.multi_asset(outs={"a": dg.AssetOut(), "b": dg.AssetOut(), "c": dg.AssetOut()})
    def abc_(context, start):
        pass

    with pytest.raises(CheckError, match="can_subset=False"):
        abc_.subset_for({dg.AssetKey("start"), dg.AssetKey("a")}, selected_asset_check_keys=None)


def test_fail_for_non_topological_order():
    @dg.multi_asset(
        outs={
            "a": dg.AssetOut(),
            "b": dg.AssetOut(),
        },
        internal_asset_deps={
            "a": set(),
            "b": {dg.AssetKey("a")},
        },
    )
    def foo():
        yield dg.Output(True, "b")
        yield dg.Output(True, "a")

    with pytest.raises(
        dg.DagsterInvariantViolationError, match='Asset "b" was yielded before its dependency "a"'
    ):
        dg.materialize_to_memory([foo])


def test_from_graph_internal_deps():
    @dg.op
    def foo():
        return 1

    @dg.op
    def bar(x):
        return x + 2

    @dg.graph(out={"a": dg.GraphOut(), "b": dg.GraphOut()})
    def baz():
        x = foo()
        return {"a": x, "b": bar(x)}

    baz_asset = AssetsDefinition.from_graph(
        baz,
        keys_by_output_name={"a": dg.AssetKey(["a"]), "b": dg.AssetKey(["b"])},
        internal_asset_deps={"a": set(), "b": {dg.AssetKey("a")}},
    )
    assert dg.materialize_to_memory([baz_asset])


def test_to_source_assets():
    @dg.asset(metadata={"a": "b"}, io_manager_key="abc", description="blablabla")
    def my_asset(): ...

    assert (
        my_asset.to_source_assets()
        == [my_asset.to_source_asset()]
        == [
            dg.SourceAsset(
                dg.AssetKey(["my_asset"]),
                metadata={"a": "b"},
                io_manager_key="abc",
                description="blablabla",
            )
        ]
    )

    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(
                key=dg.AssetKey("my_asset_name"),
                metadata={"a": "b"},
                io_manager_key="abc",
                description="blablabla",
            ),
            "my_other_out_name": dg.AssetOut(
                key=dg.AssetKey("my_other_asset"),
                metadata={"c": "d"},
                io_manager_key="def",
                description="ablablabl",
            ),
        }
    )
    def my_multi_asset():
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    my_asset_name_source_asset = dg.SourceAsset(
        dg.AssetKey(["my_asset_name"]),
        metadata={"a": "b"},
        io_manager_key="abc",
        description="blablabla",
    )
    my_other_asset_source_asset = dg.SourceAsset(
        dg.AssetKey(["my_other_asset"]),
        metadata={"c": "d"},
        io_manager_key="def",
        description="ablablabl",
    )

    assert my_multi_asset.to_source_assets() == [
        my_asset_name_source_asset,
        my_other_asset_source_asset,
    ]

    assert (
        my_multi_asset.to_source_asset(dg.AssetKey(["my_other_asset"]))
        == my_other_asset_source_asset
    )
    assert my_multi_asset.to_source_asset("my_other_asset") == my_other_asset_source_asset


def test_coerced_asset_keys():
    @dg.asset(ins={"input1": dg.AssetIn(key=["Asset", "1"])})
    def asset1(input1):
        assert input1


def test_asset_with_io_manager_def():
    events = []

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, _obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            events.append(f"entered for {context.step_key}")

        def load_input(self, _context):  # pyright: ignore[reportIncompatibleMethodOverride]
            pass

    @dg.io_manager
    def the_io_manager():
        return MyIOManager()

    @dg.asset(io_manager_def=the_io_manager)
    def the_asset():
        pass

    result = dg.materialize([the_asset])
    assert result.success
    assert events == ["entered for the_asset"]


def test_asset_with_io_manager_def_plain_old_python_object_iomanager() -> None:
    events = []

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, _obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            events.append(f"entered for {context.step_key}")

        def load_input(self, _context):  # pyright: ignore[reportIncompatibleMethodOverride]
            pass

    @dg.asset(io_manager_def=MyIOManager())
    def the_asset():
        pass

    result = dg.materialize([the_asset])
    assert result.success
    assert events == ["entered for the_asset"]


def test_multiple_assets_io_manager_defs():
    io_manager_inst = dg.InMemoryIOManager()
    num_times = [0]

    @dg.io_manager
    def the_io_manager():
        num_times[0] += 1
        return io_manager_inst

    # Under the hood, these io managers are mapped to different asset keys, so
    # we expect the io manager initialization to be called multiple times.
    @dg.asset(io_manager_def=the_io_manager)
    def the_asset():
        return 5

    @dg.asset(io_manager_def=the_io_manager)
    def other_asset():
        return 6

    dg.materialize([the_asset, other_asset])

    assert num_times[0] == 2

    the_asset_key = next(key for key in io_manager_inst.values.keys() if key[1] == "the_asset")
    assert io_manager_inst.values[the_asset_key] == 5

    other_asset_key = next(key for key in io_manager_inst.values.keys() if key[1] == "other_asset")
    assert io_manager_inst.values[other_asset_key] == 6


def test_asset_with_io_manager_key_only():
    io_manager_inst = dg.InMemoryIOManager()

    @dg.io_manager
    def the_io_manager():
        return io_manager_inst

    @dg.asset(io_manager_key="the_key")
    def the_asset():
        return 5

    dg.materialize([the_asset], resources={"the_key": the_io_manager})

    assert next(iter(io_manager_inst.values.values())) == 5


def test_asset_both_io_manager_args_provided():
    @dg.io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    def the_io_manager():
        pass

    with pytest.raises(
        CheckError,
        match=(
            "Both io_manager_key and io_manager_def were provided to `@asset` "
            "decorator. Please provide one or the other."
        ),
    ):

        @dg.asset(io_manager_key="the_key", io_manager_def=the_io_manager)
        def the_asset():
            pass


def test_asset_invocation():
    @dg.asset
    def the_asset():
        return 6

    assert the_asset() == 6


def test_asset_invocation_input():
    @dg.asset
    def input_asset(x):
        return x

    assert input_asset(5) == 5


def test_asset_invocation_resource_overrides():
    @dg.asset(required_resource_keys={"foo", "bar"})
    def asset_reqs_resources(context):
        assert context.resources.foo == "foo_resource"
        assert context.resources.bar == "bar_resource"

    asset_reqs_resources(
        dg.build_asset_context(resources={"foo": "foo_resource", "bar": "bar_resource"})
    )

    @dg.asset(
        resource_defs={
            "foo": ResourceDefinition.hardcoded_resource("orig_foo"),
            "bar": ResourceDefinition.hardcoded_resource("orig_bar"),
        }
    )
    def asset_resource_overrides(context):
        assert context.resources.foo == "override_foo"
        assert context.resources.bar == "orig_bar"

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="resource 'foo' provided on both the definition and invocation context.",
    ):
        asset_resource_overrides(dg.build_asset_context(resources={"foo": "override_foo"}))


def test_asset_invocation_resource_errors():
    @dg.asset(resource_defs={"ignored": ResourceDefinition.hardcoded_resource("not_used")})
    def asset_doesnt_use_resources():
        pass

    asset_doesnt_use_resources()

    @dg.asset(resource_defs={"used": ResourceDefinition.hardcoded_resource("foo")})
    def asset_uses_resources(context):
        assert context.resources.used == "foo"

    asset_uses_resources(dg.build_asset_context())

    @dg.asset(required_resource_keys={"foo"})
    def required_key_not_provided(_):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by op 'required_key_not_provided' was not provided."
        ),
    ):
        required_key_not_provided(dg.build_asset_context())


def test_multi_asset_resources_execution():
    class MyIOManager(dg.IOManager):
        def __init__(self, the_list):
            self._the_list = the_list

        def handle_output(self, _context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            self._the_list.append(obj)

        def load_input(self, _context):  # pyright: ignore[reportIncompatibleMethodOverride]
            pass

    foo_list = []

    @dg.resource
    def baz_resource():
        return "baz"

    @dg.io_manager(required_resource_keys={"baz"})
    def foo_manager(context):
        assert context.resources.baz == "baz"
        return MyIOManager(foo_list)

    bar_list = []

    @dg.io_manager
    def bar_manager():
        return MyIOManager(bar_list)

    @dg.multi_asset(
        outs={
            "key1": dg.AssetOut(key=dg.AssetKey("key1"), io_manager_key="foo"),
            "key2": dg.AssetOut(key=dg.AssetKey("key2"), io_manager_key="bar"),
        },
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset(context):
        # Required io manager keys are available on the context, same behavoir as ops
        assert hasattr(context.resources, "foo")
        assert hasattr(context.resources, "bar")
        yield dg.Output(1, "key1")
        yield dg.Output(2, "key2")

    with dg.instance_for_test() as instance:
        dg.materialize([my_asset], instance=instance)

    assert foo_list == [1]
    assert bar_list == [2]


def test_multi_asset_io_manager_execution_specs() -> None:
    class MyIOManager(dg.IOManager):
        def __init__(self, the_list):
            self._the_list = the_list

        def handle_output(self, _context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            assert isinstance(obj, int)
            self._the_list.append(obj)

        def load_input(self, _context):  # pyright: ignore[reportIncompatibleMethodOverride]
            pass

    foo_list = []

    @dg.resource
    def baz_resource():
        return "baz"

    @dg.io_manager(required_resource_keys={"baz"})
    def foo_manager(context):
        assert context.resources.baz == "baz"
        return MyIOManager(foo_list)

    bar_list = []

    @dg.io_manager
    def bar_manager():
        return MyIOManager(bar_list)

    @dg.multi_asset(
        specs=[
            dg.AssetSpec(
                key=dg.AssetKey("key1"),
                metadata={
                    SYSTEM_METADATA_KEY_IO_MANAGER_KEY: "foo",
                    # explicit int
                    SYSTEM_METADATA_KEY_DAGSTER_TYPE: int,
                },
            ),
            dg.AssetSpec(
                key=dg.AssetKey("key2"),
                metadata={
                    SYSTEM_METADATA_KEY_IO_MANAGER_KEY: "bar",
                    # set to Nothing
                    SYSTEM_METADATA_KEY_DAGSTER_TYPE: dg.Nothing,
                },
            ),
            dg.AssetSpec(
                key=dg.AssetKey("key3"), metadata={SYSTEM_METADATA_KEY_IO_MANAGER_KEY: "bar"}
            ),
        ],
        resource_defs={"foo": foo_manager, "bar": bar_manager, "baz": baz_resource},
    )
    def my_asset(context):
        # Required io manager keys are available on the context, same behavoir as ops
        assert hasattr(context.resources, "foo")
        assert hasattr(context.resources, "bar")
        yield dg.Output(1, "key1")
        # emit a None value, which would fail the assertion if the IOManager handled it
        yield dg.Output(None, "key2")
        yield dg.Output(2, "key3")

    assert my_asset.op.output_defs[0].dagster_type == Int
    assert my_asset.op.output_defs[1].dagster_type == Nothing
    assert my_asset.op.output_defs[2].dagster_type == Any

    with dg.instance_for_test() as instance:
        dg.materialize([my_asset], instance=instance)

    assert foo_list == [1]
    assert bar_list == [2]


def test_graph_backed_asset_resources():
    @dg.op(required_resource_keys={"foo"})
    def the_op(context):
        assert context.resources.foo == "value"
        return context.resources.foo

    @dg.graph
    def basic():
        return the_op()

    asset_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("the_asset")},
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("value")},
    )
    result = dg.materialize_to_memory([asset_provided_resources])
    assert result.success
    assert result.output_for_node("basic") == "value"

    asset_not_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("the_asset")},
    )
    result = dg.materialize_to_memory([asset_not_provided_resources], resources={"foo": "value"})
    assert result.success
    assert result.output_for_node("basic") == "value"


def test_graph_backed_asset_io_manager():
    @dg.op(required_resource_keys={"foo"}, out=dg.Out(io_manager_key="the_manager"))
    def the_op(context):
        assert context.resources.foo == "value"
        return context.resources.foo

    @dg.op
    def ingest(x):
        return x

    @dg.graph
    def basic():
        return ingest(the_op())

    events = []

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, _obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            events.append(f"entered handle_output for {context.step_key}")

        def load_input(self, context):
            events.append(f"entered handle_input for {context.upstream_output.step_key}")  # pyright: ignore[reportOptionalMemberAccess]

    asset_provided_resources = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("the_asset")},
        resource_defs={
            "foo": ResourceDefinition.hardcoded_resource("value"),
            "the_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager()),
        },
    )

    with dg.instance_for_test() as instance:
        result = dg.materialize([asset_provided_resources], instance=instance)
        assert result.success
        assert events == [
            "entered handle_output for basic.the_op",
            "entered handle_input for basic.the_op",
        ]


def test_invalid_graph_backed_assets():
    @dg.op
    def a():
        return 1

    @dg.op
    def validate(inp):
        return inp == 1

    @dg.graph
    def foo():
        a_val = a()
        validate(a_val)
        return a_val

    @dg.graph
    def bar():
        return foo()

    @dg.graph
    def baz():
        return a(), bar(), a()

    with pytest.raises(CheckError, match=r"leaf nodes.*validate"):
        AssetsDefinition.from_graph(foo)

    with pytest.raises(CheckError, match=r"leaf nodes.*bar\.validate"):
        AssetsDefinition.from_graph(bar)

    with pytest.raises(CheckError, match=r"leaf nodes.*baz\.bar\.validate"):
        AssetsDefinition.from_graph(baz)


def test_group_name_requirements():
    @dg.asset(group_name="float")  # reserved python keywords allowed
    def good_name():
        return 1

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="not a valid name in Dagster"):

        @dg.asset(group_name="bad*name")  # regex mismatch
        def bad_name():
            return 2

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Empty asset group name was provided, which is not permitted. "
            "Set group_name=None to use the default group_name or set non-empty string"
        ),
    ):

        @dg.asset(group_name="")
        def empty_name():
            return 3


def test_from_graph_w_check_specs():
    @dg.op
    def my_op():
        pass

    @dg.graph(out={"my_out": dg.GraphOut()})
    def my_graph():
        return my_op()

    my_asset = AssetsDefinition.from_graph(
        my_graph, check_specs=[dg.AssetCheckSpec("check1", asset="my_out")]
    )

    assert list(my_asset.check_specs) == [
        dg.AssetCheckSpec("check1", asset=dg.AssetKey(["my_out"]))
    ]


def test_from_graph_w_key_prefix():
    @dg.op
    def foo():
        return 1

    @dg.op
    def bar(i):
        return i + 1

    @dg.graph
    def silly_graph():
        return bar(foo())

    freshness_policy = dg.LegacyFreshnessPolicy(maximum_lag_minutes=60)
    description = "This is a description!"
    metadata = {"test_metadata": "This is some metadata"}

    the_asset = AssetsDefinition.from_graph(
        graph_def=silly_graph,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
        legacy_freshness_policies_by_output_name={"result": freshness_policy},
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

    this_is_a_prefix_the_asset_spec = the_asset.specs_by_key[
        dg.AssetKey(["this", "is", "a", "prefix", "the", "asset"])
    ]

    assert this_is_a_prefix_the_asset_spec.group_name == "abc"
    assert this_is_a_prefix_the_asset_spec.legacy_freshness_policy == freshness_policy
    assert this_is_a_prefix_the_asset_spec.description == description
    assert this_is_a_prefix_the_asset_spec.metadata == metadata

    str_prefix = AssetsDefinition.from_graph(
        graph_def=silly_graph,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey(["the", "asset"])},
        key_prefix="prefix",
    )

    assert str_prefix.keys_by_output_name["result"].path == [
        "prefix",
        "the",
        "asset",
    ]


def test_from_op_w_key_prefix():
    @dg.op
    def foo():
        return 1

    legacy_freshness_policy = dg.LegacyFreshnessPolicy(maximum_lag_minutes=60)
    description = "This is a description!"
    metadata = {"test_metadata": "This is some metadata"}

    the_asset = AssetsDefinition.from_op(
        op_def=foo,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
        legacy_freshness_policies_by_output_name={"result": legacy_freshness_policy},
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

    this_is_a_prefix_the_asset_spec = the_asset.specs_by_key[
        dg.AssetKey(["this", "is", "a", "prefix", "the", "asset"])
    ]

    assert this_is_a_prefix_the_asset_spec.group_name == "abc"
    assert this_is_a_prefix_the_asset_spec.legacy_freshness_policy == legacy_freshness_policy
    assert this_is_a_prefix_the_asset_spec.description == description
    assert this_is_a_prefix_the_asset_spec.metadata == metadata

    str_prefix = AssetsDefinition.from_op(
        op_def=foo,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey(["the", "asset"])},
        key_prefix="prefix",
    )

    assert str_prefix.keys_by_output_name["result"].path == [
        "prefix",
        "the",
        "asset",
    ]


def test_from_op_w_configured():
    @dg.op(config_schema={"bar": str})
    def foo():
        return 1

    the_asset = AssetsDefinition.from_op(op_def=foo.configured({"bar": "abc"}, name="foo2"))
    assert the_asset.keys_by_output_name["result"].path == ["foo2"]


def get_step_keys_from_run(instance: DagsterInstance, run_id: str) -> Sequence[str]:
    engine_events = list(
        instance.get_records_for_run(
            run_id=run_id, of_type=DagsterEventType.ENGINE_EVENT, ascending=False
        ).records
    )
    metadata = engine_events[0].event_log_entry.get_dagster_event().engine_event_data.metadata
    step_metadata = metadata["step_keys"]
    return ast.literal_eval(step_metadata.value)  # type: ignore


def get_num_events(instance, run_id, event_type):
    events = instance.get_records_for_run(run_id=run_id, of_type=event_type).records
    return len(events)


def test_graph_backed_asset_subset():
    @dg.op()
    def foo():
        return 1

    @dg.op
    def bar(foo):
        return foo

    @dg.graph(out={"one": dg.GraphOut(), "two": dg.GraphOut()})
    def my_graph():
        one = foo()
        return bar.alias("bar_1")(one), bar.alias("bar_2")(one)

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [AssetsDefinition.from_graph(my_graph, can_subset=True)],
            instance=instance,
            selection=[dg.AssetKey("one")],
        )
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            == 1
        )
        assert get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION) == 1
        step_keys = get_step_keys_from_run(instance, result.run_id)
        assert set(step_keys) == set(["my_graph.foo", "my_graph.bar_1"])


def test_multi_asset_output_unselected_asset():
    @dg.multi_asset(outs={"one": dg.AssetOut(), "two": dg.AssetOut()}, can_subset=True)
    def assets():
        return 1, 2

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match='Core compute for op "assets" returned an output "two" that is not selected.',
    ):
        dg.materialize([assets], selection=[dg.AssetKey("one")])


def test_graph_asset_output_unselected_asset():
    @dg.op(out={"a": dg.Out(), "b": dg.Out()})
    def foo():
        return 1, 2

    @dg.graph(out={"one": dg.GraphOut(), "two": dg.GraphOut()})
    def graph_asset():
        one, two = foo()
        return one, two

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match='Core compute for op "graph_asset.foo" returned an output "b" that is not selected.',
    ):
        dg.materialize(
            [AssetsDefinition.from_graph(graph_asset, can_subset=True)],
            selection=[dg.AssetKey("one")],
        )


def test_multi_asset_materialize_result_unselected_asset():
    @dg.multi_asset(specs=[dg.AssetSpec("one"), dg.AssetSpec("two")], can_subset=True)
    def assets():
        yield dg.MaterializeResult(asset_key=("one"))
        yield dg.MaterializeResult(asset_key=("two"))

    with pytest.raises(
        dg.DagsterInvariantViolationError, match="Asset key two not found in AssetsDefinition"
    ):
        dg.materialize([assets], selection=[dg.AssetKey("one")])


def test_multi_asset_materialize_result_unselected_asset_and_nothing():
    @dg.multi_asset(
        outs={"one": dg.AssetOut(), "two": dg.AssetOut(dagster_type=Nothing)},
        can_subset=True,
    )
    def assets():
        yield dg.Output(None, output_name="one")

    result = dg.materialize([assets], selection=[dg.AssetKey("one")])
    materializations = result.asset_materializations_for_node("assets")
    assert len(materializations) == 1
    assert materializations[0].asset_key == dg.AssetKey("one")


def test_input_subsetting_graph_backed_asset():
    @dg.asset
    def upstream_1():
        return 1

    @dg.asset
    def upstream_2():
        return 1

    @dg.op
    def bar(foo):
        return foo

    @dg.op
    def baz(up_1, up_2):
        return up_1 + up_2

    @dg.graph(out={"one": dg.GraphOut(), "two": dg.GraphOut(), "three": dg.GraphOut()})
    def my_graph(upstream_1, upstream_2):
        return (
            bar.alias("bar_1")(upstream_1),
            bar.alias("bar_2")(upstream_2),
            baz(upstream_1, upstream_2),
        )

    assets = [upstream_1, upstream_2, AssetsDefinition.from_graph(my_graph, can_subset=True)]

    with tempfile.TemporaryDirectory() as tmpdir_path:
        resources = {"io_manager": fs_io_manager.configured({"base_dir": tmpdir_path})}
        with dg.instance_for_test() as instance:
            # test first bar alias
            result = dg.materialize(
                assets,
                resources=resources,
                instance=instance,
                selection=[dg.AssetKey("one"), dg.AssetKey("upstream_1")],
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
            step_keys = get_step_keys_from_run(instance, result.run_id)
            assert set(step_keys) == set(["my_graph.bar_1", "upstream_1"])

        # test second "bar" alias
        with dg.instance_for_test() as instance:
            result = dg.materialize(
                assets,
                resources=resources,
                instance=instance,
                selection=[dg.AssetKey("two"), dg.AssetKey("upstream_2")],
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
            step_keys = get_step_keys_from_run(instance, result.run_id)
            assert set(step_keys) == set(["my_graph.bar_2", "upstream_2"])

        # test "baz" which uses both inputs
        with dg.instance_for_test() as instance:
            result = dg.materialize(
                assets,
                resources=resources,
                instance=instance,
                selection=[
                    dg.AssetKey("three"),
                    dg.AssetKey("upstream_1"),
                    dg.AssetKey("upstream_2"),
                ],
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
            step_keys = get_step_keys_from_run(instance, result.run_id)
            assert set(step_keys) == set(["my_graph.baz", "upstream_1", "upstream_2"])


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_2,num_materializations",
    [
        ([dg.AssetKey("asset_one")], {"out_1"}, None, 1),
        ([dg.AssetKey("asset_two")], {"out_2"}, {"add_one_1"}, 1),
        (
            [dg.AssetKey("asset_two"), dg.AssetKey("asset_three")],
            {"out_2"},
            {"add_one_1", "add_one_2"},
            2,
        ),
        (
            [dg.AssetKey("asset_one"), dg.AssetKey("asset_two"), dg.AssetKey("asset_three")],
            {"out_1", "out_2"},
            {"add_one_1", "add_one_2"},
            3,
        ),
    ],
)
def test_graph_backed_asset_subset_context(
    asset_selection, selected_output_names_op_1, selected_output_names_op_2, num_materializations
):
    @dg.op(out={"out_1": dg.Out(is_required=False), "out_2": dg.Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        assert (num_materializations != 3) == context.is_subset
        if "out_1" in context.selected_output_names:
            yield dg.Output(1, output_name="out_1")
        if "out_2" in context.selected_output_names:
            yield dg.Output(1, output_name="out_2")

    @dg.op(out={"add_one_1": dg.Out(is_required=False), "add_one_2": dg.Out(is_required=False)})
    def add_one(context, x):
        assert context.selected_output_names == selected_output_names_op_2
        assert (num_materializations != 3) == context.is_subset
        if "add_one_1" in context.selected_output_names:
            yield dg.Output(x, output_name="add_one_1")
        if "add_one_2" in context.selected_output_names:
            yield dg.Output(x, output_name="add_one_2")

    @dg.graph(
        out={"asset_one": dg.GraphOut(), "asset_two": dg.GraphOut(), "asset_three": dg.GraphOut()}
    )
    def three():
        out_1, reused_output = op_1()
        out_2, out_3 = add_one(reused_output)
        return {"asset_one": out_1, "asset_two": out_2, "asset_three": out_3}

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [AssetsDefinition.from_graph(three, can_subset=True)],
            selection=asset_selection,
            instance=instance,
        )
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


def test_graph_backed_asset_subset_two_routes():
    """Only asset2 is selected.

    Materializating asset2 requires executing op2, whose in2 is hooked up to op1's out2. op1's out2
    does not correspond to any asset, so the only way to get it is to execute op1. Thus, op1 is
    executed. op1's out1 is linked to asset1, so asset1 is also materialized, even though it is not
    selected.
    """

    @dg.op(out={"out1": dg.Out(is_required=False), "out2": dg.Out(is_required=False)})
    def op1(context):
        for output_name in context.selected_output_names:
            yield dg.Output(None, output_name=output_name)

    @dg.op(ins={"in1": dg.In(dg.Nothing), "in2": dg.In(dg.Nothing)})
    def op2(context) -> None:
        assert context.asset_key_for_input("in1") == dg.AssetKey("asset1")

    @dg.graph_multi_asset(
        outs={
            "out1": dg.AssetOut(key="asset1"),
            "out2": dg.AssetOut(key="asset2"),
        },
        can_subset=True,
    )
    def assets():
        op1_out1, op1_out2 = op1()
        return op1_out1, op2(in1=op1_out1, in2=op1_out2)

    result = dg.materialize([assets], selection=["asset2"])
    assert result.success
    materialized_assets = [
        event.event_specific_data.materialization.asset_key  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        for event in result.get_asset_materialization_events()
    ]
    assert materialized_assets == [dg.AssetKey("asset2")]


def test_graph_backed_asset_subset_two_routes_yield_only_selected():
    @dg.op(out={"out1": dg.Out(is_required=False), "out2": dg.Out(is_required=False)})
    def op1():
        yield dg.Output(None, output_name="out2")

    @dg.op(ins={"in1": dg.In(dg.Nothing), "in2": dg.In(dg.Nothing)})
    def op2(context) -> None:
        assert context.asset_key_for_input("in1") == dg.AssetKey("asset1")

    @dg.graph_multi_asset(
        outs={
            "out1": dg.AssetOut(key="asset1"),
            "out2": dg.AssetOut(key="asset2"),
        },
        can_subset=True,
    )
    def assets():
        op1_out1, op1_out2 = op1()
        return op1_out1, op2(in1=op1_out1, in2=op1_out2)

    result = dg.materialize([assets], selection=["asset2"])
    assert result.success
    materialized_assets = [
        event.event_specific_data.materialization.asset_key  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        for event in result.get_asset_materialization_events()
    ]
    assert materialized_assets == [dg.AssetKey("asset2")]


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_3,num_materializations",
    [
        ([dg.AssetKey("asset_one")], {"out_1"}, None, 1),
        ([dg.AssetKey("asset_two")], {"out_2"}, {"op_3_1"}, 1),
        (
            [dg.AssetKey("asset_two"), dg.AssetKey("asset_three")],
            {"out_2"},
            {"op_3_1", "op_3_2"},
            2,
        ),
        (
            [dg.AssetKey("asset_four"), dg.AssetKey("asset_three")],
            {"out_1", "out_2"},
            {"op_3_2"},
            2,
        ),
        ([dg.AssetKey("asset_one"), dg.AssetKey("asset_four")], {"out_1"}, None, 2),
        (
            [
                dg.AssetKey("asset_one"),
                dg.AssetKey("asset_two"),
                dg.AssetKey("asset_three"),
                dg.AssetKey("asset_four"),
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
    @dg.op(out={"out_1": dg.Out(is_required=False), "out_2": dg.Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        if "out_1" in context.selected_output_names:
            yield dg.Output(1, output_name="out_1")
        if "out_2" in context.selected_output_names:
            yield dg.Output(1, output_name="out_2")

    @dg.op(ins={"x": dg.In(dg.Nothing)})
    def op_2():
        return None

    @dg.op(
        out={"op_3_1": dg.Out(is_required=False), "op_3_2": dg.Out(is_required=False)},
        ins={"x": dg.In(dg.Nothing)},
    )
    def op_3(context):
        assert context.selected_output_names == selected_output_names_op_3
        if "op_3_1" in context.selected_output_names:
            yield dg.Output(None, output_name="op_3_1")
        if "op_3_2" in context.selected_output_names:
            yield dg.Output(None, output_name="op_3_2")

    @dg.graph(
        out={
            "asset_one": dg.GraphOut(),
            "asset_two": dg.GraphOut(),
            "asset_three": dg.GraphOut(),
            "asset_four": dg.GraphOut(),
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

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [AssetsDefinition.from_graph(graph_asset, can_subset=True)],
            selection=asset_selection,
            instance=instance,
        )
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


@pytest.mark.parametrize(
    "asset_selection,selected_output_names_op_1,selected_output_names_op_2,num_materializations",
    [
        ([dg.AssetKey("a")], {"op_1_1"}, None, 1),
        ([dg.AssetKey("b")], {"op_1_2"}, None, 1),
        ([dg.AssetKey("c")], {"op_1_2"}, {"op_2_1"}, 1),
        ([dg.AssetKey("c"), dg.AssetKey("d")], {"op_1_2"}, {"op_2_1", "op_2_2"}, 2),
        ([dg.AssetKey("b"), dg.AssetKey("d")], {"op_1_2"}, {"op_2_2"}, 2),
    ],
)
def test_nested_graph_subset_context(
    asset_selection, selected_output_names_op_1, selected_output_names_op_2, num_materializations
):
    @dg.op(out={"op_1_1": dg.Out(is_required=False), "op_1_2": dg.Out(is_required=False)})
    def op_1(context):
        assert context.selected_output_names == selected_output_names_op_1
        if "op_1_1" in context.selected_output_names:
            yield dg.Output(1, output_name="op_1_1")
        if "op_1_2" in context.selected_output_names:
            yield dg.Output(1, output_name="op_1_2")

    @dg.op(
        out={"op_2_1": dg.Out(is_required=False), "op_2_2": dg.Out(is_required=False)},
        ins={"x": dg.In(dg.Nothing)},
    )
    def op_2(context):
        assert context.selected_output_names == selected_output_names_op_2
        if "op_2_2" in context.selected_output_names:
            yield dg.Output(None, output_name="op_2_2")
        if "op_2_1" in context.selected_output_names:
            yield dg.Output(None, output_name="op_2_1")

    @dg.graph(out={"a": dg.GraphOut(), "b": dg.GraphOut()})
    def two_outputs_graph():
        a, b = op_1()
        return {"a": a, "b": b}

    @dg.graph(out={"c": dg.GraphOut(), "d": dg.GraphOut()})
    def downstream_graph(b):
        c, d = op_2(b)
        return {"c": c, "d": d}

    @dg.graph(out={"a": dg.GraphOut(), "b": dg.GraphOut(), "c": dg.GraphOut(), "d": dg.GraphOut()})
    def nested_graph():
        a, b = two_outputs_graph()  # pyright: ignore[reportGeneralTypeIssues]
        c, d = downstream_graph(b)  # pyright: ignore[reportGeneralTypeIssues]
        return {"a": a, "b": b, "c": c, "d": d}

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [AssetsDefinition.from_graph(nested_graph, can_subset=True)],
            selection=asset_selection,
            instance=instance,
        )
        assert result.success
        assert (
            get_num_events(instance, result.run_id, DagsterEventType.ASSET_MATERIALIZATION)
            == num_materializations
        )


def test_graph_backed_asset_reused():
    @dg.asset
    def upstream():
        return 1

    @dg.op
    def foo(upstream):
        return 1

    @dg.graph
    def graph_asset(upstream):
        return foo(upstream)

    @dg.asset
    def one_downstream(asset_one):
        return asset_one

    @dg.asset
    def duplicate_one_downstream(duplicate_one):
        return duplicate_one

    with tempfile.TemporaryDirectory() as tmpdir_path:
        asset_job = dg.define_asset_job("yay").resolve(
            asset_graph=AssetGraph.from_assets(
                dg.with_resources(
                    [
                        upstream,
                        AssetsDefinition.from_graph(
                            graph_asset,
                            keys_by_output_name={
                                "result": dg.AssetKey("asset_one"),
                            },
                            can_subset=True,
                        ),
                        AssetsDefinition.from_graph(
                            graph_asset,
                            keys_by_output_name={
                                "result": dg.AssetKey("duplicate_one"),
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
        asset_one_dep_op_handles = asset_job.asset_layer.upstream_dep_op_handles(
            dg.AssetKey("asset_one")
        )
        duplicate_one_dep_op_handles = asset_job.asset_layer.upstream_dep_op_handles(
            dg.AssetKey("duplicate_one")
        )
        assert asset_one_dep_op_handles != duplicate_one_dep_op_handles

        with dg.instance_for_test() as instance:
            asset_job.execute_in_process(
                instance=instance, asset_selection=[dg.AssetKey("upstream")]
            )
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[dg.AssetKey("asset_one"), dg.AssetKey("one_downstream")],
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
            step_keys = get_step_keys_from_run(instance, result.run_id)
            assert set(step_keys) == set(["graph_asset.foo", "one_downstream"])

            # Other graph-backed asset
            result = asset_job.execute_in_process(
                instance=instance,
                asset_selection=[
                    dg.AssetKey("duplicate_one"),
                    dg.AssetKey("duplicate_one_downstream"),
                ],
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
            step_keys = get_step_keys_from_run(instance, result.run_id)
            assert set(step_keys) == set(["graph_asset.foo", "duplicate_one_downstream"])


def test_self_dependency():
    @dg.asset(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
        ins={
            "a": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def a(a):
        del a

    class MyIOManager(dg.IOManager):
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
                assert context.asset_partition_key_range == dg.PartitionKeyRange(
                    "2020-01-01", "2020-01-01"
                )
                assert context.has_asset_partitions

    resources = {"io_manager": MyIOManager()}
    dg.materialize([a], partition_key="2020-01-01", resources=resources)
    dg.materialize([a], partition_key="2020-01-02", resources=resources)


def test_context_assets_def():
    @dg.asset
    def a(context):
        assert context.assets_def.keys == {a.key}
        return 1

    @dg.asset
    def b(context, a):
        assert context.assets_def.keys == {b.key}
        return 2

    dg.materialize([a, b])


def test_invalid_context_assets_def():
    @dg.op
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

    @dg.asset(resource_defs={"bare_resource": BareObjectResource()})
    def blah(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    defs = dg.Definitions(assets=[blah])
    defs.resolve_implicit_global_asset_job_def().execute_in_process()
    assert executed["yes"]


def test_asset_key_with_prefix():
    assert dg.AssetKey("foo").with_prefix("prefix") == dg.AssetKey(["prefix", "foo"])
    assert dg.AssetKey("foo").with_prefix(["prefix_one", "prefix_two"]) == dg.AssetKey(
        ["prefix_one", "prefix_two", "foo"]
    )

    with pytest.raises(CheckError):
        dg.AssetKey("foo").with_prefix(1)  # pyright: ignore[reportArgumentType]


def _exec_asset(asset_def, selection=None):
    result = dg.materialize([asset_def], selection=selection)
    assert result.success
    return result.asset_materializations_for_node(asset_def.node_def.name)


def test_multi_asset_return_none():
    #
    # non-optional Nothing
    #
    @dg.multi_asset(
        outs={
            "asset1": dg.AssetOut(dagster_type=Nothing),
            "asset2": dg.AssetOut(dagster_type=Nothing),
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
    @dg.multi_asset(
        outs={
            "asset1": dg.AssetOut(dagster_type=Nothing, is_required=False),
            "asset2": dg.AssetOut(dagster_type=Nothing, is_required=False),
        },
        can_subset=True,
    )
    def subset(context: AssetExecutionContext):
        # ...use context.selected_asset_keys materialize subset of assets without IO manager
        pass

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        _exec_asset(subset)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        subset(dg.build_asset_context())

    #
    # untyped (fails)
    #
    @dg.multi_asset(
        outs={
            "asset1": dg.AssetOut(),
            "asset2": dg.AssetOut(),
        },
    )
    def untyped():
        # ...materialize assets without IO manager
        pass

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        _exec_asset(untyped)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped()


def test_direct_instantiation_invalid_partition_mapping():
    @dg.op
    def my_op():
        return 1

    with pytest.raises(CheckError, match="received a partition mapping"):
        dg.AssetsDefinition(
            keys_by_input_name={},
            keys_by_output_name={"result": dg.AssetKey("foo")},
            node_def=my_op,
            partition_mappings={dg.AssetKey("nonexistent_asset"): dg.IdentityPartitionMapping()},
        )


def test_return_materialization():
    #
    # status quo - use add add_output_metadata
    #
    @dg.asset
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
    @dg.asset
    def logged(context: AssetExecutionContext):
        context.log_event(
            dg.AssetMaterialization(
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
    @dg.asset
    def ret_untyped(context: AssetExecutionContext):
        return dg.MaterializeResult(
            metadata={"one": 1},
        )

    mats = _exec_asset(ret_untyped)
    assert len(mats) == 1, mats
    assert "one" in mats[0].metadata
    assert mats[0].tags

    #
    # key mismatch
    #
    @dg.asset
    def ret_mismatch(context: AssetExecutionContext):
        return dg.MaterializeResult(
            asset_key="random",
            metadata={"one": 1},
        )

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Asset key random not found in AssetsDefinition",
    ):
        mats = _exec_asset(ret_mismatch)


def test_multi_asset_no_out():
    #
    # base case
    #
    table_A = dg.AssetSpec("table_A")
    table_B = dg.AssetSpec("table_B")

    @dg.multi_asset(specs=[table_A, table_B])
    def basic():
        pass

    mats = _exec_asset(basic)

    result = basic()
    assert result is None

    #
    # internal deps
    #
    table_C = dg.AssetSpec("table_C", deps=[table_A, table_B])

    @dg.multi_asset(specs=[table_A, table_B, table_C])
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
    @dg.multi_asset(
        specs=[table_A, table_B],
        can_subset=True,
    )
    def basic_subset(context: AssetExecutionContext):
        for key in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key=key)

    mats = _exec_asset(basic_subset, ["table_A"])
    assert table_A.key in {mat.asset_key for mat in mats}
    assert table_B.key not in {mat.asset_key for mat in mats}

    # selected_asset_keys breaks direct invocation
    # basic_subset(build_asset_context())

    #
    # optional
    #
    @dg.multi_asset(
        specs=[table_A, dg.AssetSpec("table_B", skippable=True)],
    )
    def basic_optional(context: AssetExecutionContext):
        yield dg.MaterializeResult(asset_key="table_A")

    mats = _exec_asset(basic_optional)
    assert table_A.key in {mat.asset_key for mat in mats}
    assert table_B.key not in {mat.asset_key for mat in mats}

    basic_optional(dg.build_asset_context())

    #
    # metadata
    #
    @dg.multi_asset(specs=[table_A, table_B])
    def metadata(context: AssetExecutionContext):
        yield dg.MaterializeResult(asset_key="table_A", metadata={"one": 1})
        yield dg.MaterializeResult(asset_key="table_B", metadata={"two": 2})

    mats = _exec_asset(metadata)
    assert len(mats) == 2
    assert mats[0].metadata["one"]
    assert mats[1].metadata["two"]

    # yielded event processing unresolved for assets
    # results = list(metadata(build_asset_context()))
    # assert len(results) == 2


def test_multi_asset_nodes_out_names():
    sales_users = dg.AssetSpec(["sales", "users"])
    marketing_users = dg.AssetSpec(["marketing", "users"])

    @dg.multi_asset(specs=[sales_users, marketing_users])
    def users():
        pass

    assert len(users.op.output_defs) == 2
    assert {out_def.name for out_def in users.op.output_defs} == {
        "sales__users",
        "marketing__users",
    }


def test_multi_asset_dependencies_captured_in_internal_asset_deps() -> None:
    @dg.asset
    def my_upstream_asset() -> int:
        return 1

    with pytest.raises(CheckError, match="inputs must be associated with an output"):

        @dg.multi_asset(outs={"asset_one": dg.AssetOut()}, internal_asset_deps={"asset_one": set()})
        def my_multi_asset(my_upstream_asset: int) -> int:
            return my_upstream_asset + 1


def test_asset_spec_deps():
    @dg.asset
    def table_A():
        pass

    table_b = dg.AssetSpec("table_B", deps=[table_A])
    table_c = dg.AssetSpec("table_C", deps=[table_A, table_b])
    table_b_no_dep = dg.AssetSpec("table_B")
    table_c_no_dep = dg.AssetSpec("table_C")

    @dg.multi_asset(specs=[table_b, table_c])
    def deps_in_specs(): ...

    result = dg.materialize([deps_in_specs, table_A])
    assert result.success
    mats = result.get_asset_materialization_events()
    assert len(mats) == 3
    # first event should be A materialization
    assert mats[0].asset_key == table_A.key

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Can not pass deps and specs"):

        @dg.multi_asset(specs=[table_b_no_dep, table_c_no_dep], deps=["table_A"])
        def no_deps_in_specs(): ...

    @dg.multi_asset(specs=[table_b, table_c])
    def also_input(table_A): ...

    result = dg.materialize([also_input, table_A])
    assert result.success
    mats = result.get_asset_materialization_events()
    assert len(mats) == 3
    # first event should be A materialization
    assert mats[0].asset_key == table_A.key

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="specified as AssetIns",
    ):

        @dg.multi_asset(specs=[table_b, table_c])
        def rogue_input(table_X): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="specified as AssetIns",
    ):

        @dg.multi_asset(specs=[table_b_no_dep, table_c_no_dep])
        def no_spec_deps_but_input(table_A): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="specify deps on the AssetSpecs directly",
    ):

        @dg.multi_asset(
            specs=[table_b_no_dep, table_c_no_dep],
            deps=[table_A],
        )
        def use_deps(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="specify deps on the AssetSpecs directly",
    ):

        @dg.multi_asset(
            specs=[table_b_no_dep, table_c_no_dep],
            internal_asset_deps={"table_C": {dg.AssetKey("table_B")}},
        )
        def use_internal_deps(): ...


def test_asset_key_on_context():
    @dg.asset
    def test_asset_key_on_context(context: AssetExecutionContext):
        assert context.asset_key == dg.AssetKey(["test_asset_key_on_context"])

    @dg.asset(key_prefix=["a_prefix"])
    def test_asset_key_on_context_with_prefix(context: AssetExecutionContext):
        assert context.asset_key == dg.AssetKey(
            ["a_prefix", "test_asset_key_on_context_with_prefix"]
        )

    dg.materialize([test_asset_key_on_context, test_asset_key_on_context_with_prefix])


def test_multi_asset_asset_key_on_context():
    @dg.multi_asset(
        outs={
            "my_string_asset": dg.AssetOut(),
        }
    )
    def asset_key_context(context: AssetExecutionContext):
        assert context.asset_key == dg.AssetKey(["my_string_asset"])

    dg.materialize([asset_key_context])

    @dg.multi_asset(
        outs={
            "my_string_asset": dg.AssetOut(),
            "my_int_asset": dg.AssetOut(),
        }
    )
    def two_assets_key_context(context: AssetExecutionContext):
        return context.asset_key, 12

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Cannot call `context.asset_key` in a multi_asset with more than one asset",
    ):
        dg.materialize([two_assets_key_context])

    # test with AssetSpecs

    spec1 = dg.AssetSpec(key="spec1")

    @dg.multi_asset(specs=[spec1])
    def asset_key_context_with_specs(context: AssetExecutionContext):
        assert context.asset_key == dg.AssetKey(["spec1"])

    dg.materialize([asset_key_context_with_specs])

    spec2 = dg.AssetSpec(key="spec2")
    spec3 = dg.AssetSpec(key="spec3")

    @dg.multi_asset(specs=[spec2, spec3])
    def asset_key_context_with_two_specs(context: AssetExecutionContext):
        context.log.info(context.asset_key)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Cannot call `context.asset_key` in a multi_asset with more than one asset",
    ):
        dg.materialize([asset_key_context_with_two_specs])


def test_graph_asset_explicit_coercible_key() -> None:
    @dg.op
    def my_op() -> int:
        return 1

    # conversion
    @graph_asset(key="my_graph_asset")
    def _specified_elsewhere() -> int:
        return my_op()

    assert _specified_elsewhere.key == dg.AssetKey(["my_graph_asset"])


def test_graph_asset_explicit_fully_key() -> None:
    @dg.op
    def my_op() -> int:
        return 1

    @graph_asset(key=dg.AssetKey("my_graph_asset"))
    def _specified_elsewhere() -> int:
        return my_op()

    assert _specified_elsewhere.key == dg.AssetKey(["my_graph_asset"])


def test_graph_asset_cannot_use_key_prefix_name_and_key() -> None:
    @dg.op
    def my_op() -> int:
        return 1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(key_prefix="a_prefix", key=dg.AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(name="a_name", key=dg.AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Cannot specify a name or key prefix for @graph_asset when the key argument is provided"
        ),
    ):

        @graph_asset(name="a_name", key_prefix="a_prefix", key=dg.AssetKey("my_graph_asset"))
        def _specified_elsewhere() -> int:
            return my_op()

        assert _specified_elsewhere  # appease linter


def test_asset_owners():
    @dg.asset(owners=["team:team1", "claire@dagsterlabs.com"])
    def my_asset():
        pass

    assert my_asset.specs_by_key[my_asset.key].owners == ["team:team1", "claire@dagsterlabs.com"]
    assert (
        my_asset.with_attributes().specs_by_key[my_asset.key].owners
        == my_asset.specs_by_key[my_asset.key].owners
    )  # copies ok

    @dg.asset(owners=[])
    def asset2():
        pass

    assert asset2.specs_by_key[asset2.key].owners == []

    @dg.asset(owners=None)
    def asset3():
        pass

    assert asset3.specs_by_key[asset3.key].owners == []


def test_invalid_asset_owners():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Owner must be an email address or a team name prefixed with 'team:'",
    ):

        @dg.asset(owners=["arbitrary string"])
        def my_asset():
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Owner must be an email address or a team name prefixed with 'team:'",
    ):

        @dg.asset(owners=["notanemail@com"])
        def my_asset_2():
            pass


def test_multi_asset_owners():
    @dg.multi_asset(
        outs={
            "out1": dg.AssetOut(owners=["team:team1", "user@dagsterlabs.com"]),
            "out2": dg.AssetOut(owners=["user2@dagsterlabs.com"]),
        }
    )
    def my_multi_asset():
        pass

    assert my_multi_asset.specs_by_key[dg.AssetKey("out1")].owners == [
        "team:team1",
        "user@dagsterlabs.com",
    ]
    assert my_multi_asset.specs_by_key[dg.AssetKey("out2")].owners == ["user2@dagsterlabs.com"]


def test_replace_asset_keys_for_asset_with_owners():
    @dg.multi_asset(
        outs={
            "out1": dg.AssetOut(owners=["user@dagsterlabs.com"]),
            "out2": dg.AssetOut(owners=["user@dagsterlabs.com"]),
        }
    )
    def my_multi_asset():
        pass

    assert my_multi_asset.specs_by_key[dg.AssetKey("out1")].owners == ["user@dagsterlabs.com"]
    assert my_multi_asset.specs_by_key[dg.AssetKey("out2")].owners == ["user@dagsterlabs.com"]

    prefixed_asset = my_multi_asset.with_attributes(
        asset_key_replacements={dg.AssetKey(["out1"]): dg.AssetKey(["prefix", "out1"])}
    )
    assert prefixed_asset.specs_by_key[dg.AssetKey(["prefix", "out1"])].owners == [
        "user@dagsterlabs.com"
    ]
    assert prefixed_asset.specs_by_key[dg.AssetKey("out2")].owners == ["user@dagsterlabs.com"]


def test_asset_spec_with_code_versions():
    @dg.multi_asset(
        specs=[dg.AssetSpec(key="a", code_version="1"), dg.AssetSpec(key="b", code_version="2")]
    )
    def multi_asset_with_versions():
        yield dg.MaterializeResult("a")
        yield dg.MaterializeResult("b")

    code_versions_by_key = {spec.key: spec.code_version for spec in multi_asset_with_versions.specs}
    assert code_versions_by_key == {dg.AssetKey(["a"]): "1", dg.AssetKey(["b"]): "2"}


def test_asset_spec_with_metadata():
    @dg.multi_asset(
        specs=[
            dg.AssetSpec(key="a", metadata={"foo": "1"}),
            dg.AssetSpec(key="b", metadata={"bar": "2"}),
        ]
    )
    def multi_asset_with_metadata():
        yield dg.MaterializeResult("a")
        yield dg.MaterializeResult("b")

    metadata_by_key = {spec.key: spec.metadata for spec in multi_asset_with_metadata.specs}
    assert metadata_by_key == {dg.AssetKey(["a"]): {"foo": "1"}, dg.AssetKey(["b"]): {"bar": "2"}}


def test_asset_with_tags():
    @dg.asset(tags={"a": "b"})
    def asset1(): ...

    assert asset1.specs_by_key[asset1.key].tags == {"a": "b"}

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag keys"):

        @dg.asset(tags={"a%": "b"})  # key has illegal character
        def asset2(): ...


def test_asset_spec_with_tags():
    @dg.multi_asset(specs=[dg.AssetSpec("asset1", tags={"a": "b"})])
    def assets(): ...

    assert assets.specs_by_key[dg.AssetKey("asset1")].tags == {"a": "b"}

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag key"):

        @dg.multi_asset(
            specs=[dg.AssetSpec("asset1", tags={"a%": "b"})]
        )  # key has illegal character
        def assets(): ...


def test_asset_decorator_with_kinds() -> None:
    @dg.asset(kinds={"python"})
    def asset1():
        pass

    assert asset1.specs_by_key[dg.AssetKey("asset1")].kinds == {"python"}

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Assets can have at most three kinds currently."
    ):

        @dg.asset(kinds={"python", "snowflake", "bigquery", "airflow"})
        def asset2(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot specify compute_kind and kinds on the @asset decorator.",
    ):

        @dg.asset(compute_kind="my_compute_kind", kinds={"python"})
        def asset3(): ...


def test_asset_spec_with_kinds() -> None:
    @dg.multi_asset(specs=[dg.AssetSpec("asset1", kinds={"python"})])
    def assets(): ...

    assert assets.specs_by_key[dg.AssetKey("asset1")].kinds == {"python"}

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Assets can have at most three kinds currently."
    ):

        @dg.multi_asset(
            specs=[dg.AssetSpec("asset1", kinds={"python", "snowflake", "bigquery", "airflow"})]
        )
        def assets2(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Can not specify compute_kind on both the @multi_asset and kinds on AssetSpecs.",
    ):

        @dg.multi_asset(
            compute_kind="my_compute_kind", specs=[dg.AssetSpec("asset1", kinds={"python"})]
        )
        def assets3(): ...


def test_asset_out_with_tags():
    @dg.multi_asset(outs={"asset1": dg.AssetOut(tags={"a": "b"})})
    def assets(): ...

    assert assets.specs_by_key[dg.AssetKey("asset1")].tags == {"a": "b"}

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag key"):

        @dg.multi_asset(outs={"asset1": dg.AssetOut(tags={"a%": "b"})})  # key has illegal character
        def assets(): ...


def test_asset_out_with_kinds():
    @dg.multi_asset(outs={"asset1": dg.AssetOut(kinds={"a", "b"})})
    def assets(): ...

    assert assets.specs_by_key[dg.AssetKey("asset1")].kinds == {"a", "b"}

    # the error contains "tag" because that's how kinds are currently implemented
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag key"):

        @dg.multi_asset(
            outs={"asset1": dg.AssetOut(kinds={"a%", "b"})}
        )  # key has illegal character
        def assets(): ...


def test_asset_spec_skippable():
    @dg.op(out=dg.Out(is_required=False))
    def op1():
        pass

    assets_def = dg.AssetsDefinition(
        node_def=op1, keys_by_output_name={"result": dg.AssetKey("asset1")}, keys_by_input_name={}
    )
    assert next(iter(assets_def.specs)).skippable


def test_construct_assets_definition_no_args() -> None:
    with pytest.raises(CheckError, match="If specs are not provided, a node_def must be provided"):
        dg.AssetsDefinition()


def test_construct_assets_definition_without_node_def() -> None:
    spec = dg.AssetSpec("asset1", tags={"foo": "bar"}, group_name="hello")
    assets_def = dg.AssetsDefinition(specs=[spec])
    assert not assets_def.is_executable
    assert list(assets_def.specs) == [spec]


def test_construct_assets_definition_without_node_def_attr_by_keys() -> None:
    with pytest.raises(CheckError):
        dg.AssetsDefinition(group_names_by_key={dg.AssetKey("foo"): "foo_group"})


def test_construct_assets_definition_without_node_def_with_bad_param_combo() -> None:
    spec = dg.AssetSpec("asset1", tags={"foo": "bar"}, group_name="hello")
    with pytest.raises(CheckError):
        dg.AssetsDefinition(specs=[spec], backfill_policy=BackfillPolicy.single_run())

    with pytest.raises(CheckError):
        dg.AssetsDefinition(specs=[spec], keys_by_input_name={"input": dg.AssetKey("asset0")})

    with pytest.raises(CheckError):
        dg.AssetsDefinition(specs=[spec], keys_by_output_name={"result": dg.AssetKey("asset1")})

    with pytest.raises(CheckError):
        dg.AssetsDefinition(specs=[spec], can_subset=True)


def test_multiple_partition_defs_allowed_without_node_def() -> None:
    spec1 = dg.AssetSpec(
        "asset1", partitions_def=dg.StaticPartitionsDefinition(["a", "b"]), group_name="default"
    )
    spec2 = dg.AssetSpec(
        "asset2", partitions_def=dg.StaticPartitionsDefinition(["x", "y"]), group_name="default"
    )
    assets_def = dg.AssetsDefinition(specs=[spec1, spec2])
    assert not assets_def.is_executable
    assert list(assets_def.specs) == [spec1, spec2]


def test_multiple_keys_per_output_name():
    @dg.op(out={"out1": dg.Out(), "out2": dg.Out()})
    def op1():
        pass

    with pytest.raises(CheckError, match="Each asset key should correspond to a single output."):
        dg.AssetsDefinition(
            node_def=op1, keys_by_output_name={"out1": dg.AssetKey("a"), "out2": dg.AssetKey("a")}
        )


def test_iterate_over_single_key() -> None:
    key = dg.AssetKey("ouch")
    with pytest.raises(
        Exception,
        match="Iteration is not allowed",
    ):
        [_ for _ in key]  # type: ignore # good job type checker


def test_index_in_to_key() -> None:
    key = dg.AssetKey("ouch")
    with pytest.raises(
        Exception,
        match="Index access is not allowed",
    ):
        key[0][0]  # type: ignore # good job type checker


def test_asset_dep_backcompat() -> None:
    # AssetKey used to be an iterable tuple, which unintentionally made this work so continue supporting it

    @dg.asset(deps=dg.AssetKey("oops"))  # type: ignore # good job type checker
    def _(): ...


def test_unpartitioned_asset_metadata():
    @dg.asset
    def unpartitioned_asset(context: AssetExecutionContext) -> None:
        context.add_asset_metadata(metadata={"asset_unpartitioned": "yay"})
        context.add_output_metadata(metadata={"output_unpartitioned": "yay"})

        context.add_asset_metadata(
            asset_key="unpartitioned_asset", metadata={"asset_key_specified": "yay"}
        )
        context.add_output_metadata(
            output_name=context.assets_def.get_output_name_for_asset_key(context.assets_def.key),
            metadata={"output_name_specified": "yay"},
        )

        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, partition_key="nonce")

        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, asset_key="nonce")

        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_output_metadata(metadata={"wont_work": "yay"}, output_name="nonce")

    with dg.instance_for_test() as instance:
        result = dg.materialize(assets=[unpartitioned_asset], instance=instance)
        assert result.success

        asset_materializations = result.asset_materializations_for_node("unpartitioned_asset")
        assert len(asset_materializations) == 1
        assert asset_materializations[0].metadata == {
            "asset_unpartitioned": dg.TextMetadataValue("yay"),
            "output_unpartitioned": dg.TextMetadataValue("yay"),
            "asset_key_specified": dg.TextMetadataValue("yay"),
            "output_name_specified": dg.TextMetadataValue("yay"),
        }

        output_log = instance.get_event_records(
            event_records_filter=dg.EventRecordsFilter(event_type=DagsterEventType.STEP_OUTPUT)
        )[0]
        assert check.not_none(
            output_log.event_log_entry.dagster_event
        ).step_output_data.metadata == {
            "output_unpartitioned": dg.TextMetadataValue("yay"),
            "output_name_specified": dg.TextMetadataValue("yay"),
        }


def test_unpartitioned_multiasset_metadata():
    @dg.multi_asset(specs=[dg.AssetSpec("a"), dg.AssetSpec("b")])
    def compute(context: AssetExecutionContext):
        # Won't work because no asset key
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"})
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, partition_key="nonce")

        # Won't work because wrong asset key
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(metadata={"wont_work": "yay"}, asset_key="nonce")

        # Won't work because no output name
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_output_metadata(metadata={"wont_work": "yay"})

        # Won't work because wrong output name
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_output_metadata(metadata={"wont_work": "yay"}, output_name="nonce")

        # Won't work because partition key
        with pytest.raises(dg.DagsterInvariantViolationError):
            context.add_asset_metadata(
                metadata={"wont_work": "yay"}, asset_key="a", partition_key="nonce"
            )

        context.add_asset_metadata(asset_key="a", metadata={"asset_key_specified": "yay"})
        context.add_asset_metadata(asset_key="b", metadata={"asset_key_specified": "yay"})
        context.add_output_metadata(
            output_name=context.assets_def.get_output_name_for_asset_key(dg.AssetKey("a")),
            metadata={"output_name_specified": "yay"},
        )
        context.add_asset_metadata(metadata={"additional_a_metadata": "yay"}, asset_key="a")

        context.add_output_metadata(
            output_name=context.assets_def.get_output_name_for_asset_key(dg.AssetKey("a")),
            metadata={"additional_a_output_metadata": "yay"},
        )

    with dg.instance_for_test() as instance:
        result = dg.materialize(assets=[compute], instance=instance)
        assert result.success

        asset_materializations = result.asset_materializations_for_node("compute")
        assert len(asset_materializations) == 2
        a_mat = next(mat for mat in asset_materializations if mat.asset_key == dg.AssetKey("a"))
        assert set(a_mat.metadata.keys()) == {
            "asset_key_specified",
            "output_name_specified",
            "additional_a_metadata",
            "additional_a_output_metadata",
        }
        b_mat = next(mat for mat in asset_materializations if mat.asset_key == dg.AssetKey("b"))
        assert set(b_mat.metadata.keys()) == {"asset_key_specified"}

        output_logs = instance.get_event_records(
            event_records_filter=dg.EventRecordsFilter(event_type=DagsterEventType.STEP_OUTPUT)
        )
        output_event = next(
            check.not_none(log.event_log_entry.dagster_event).step_output_data.metadata
            for log in output_logs
            if check.not_none(
                log.event_log_entry.dagster_event
            ).step_output_data.step_output_handle.output_name
            == "a"
        )
        assert set(output_event.keys()) == {
            "output_name_specified",
            "additional_a_output_metadata",
        }


def test_execute_unselected_asset_check():
    """Test the behavior that we allow yielding a check result for an unselected but well-specified asset check."""

    @dg.multi_asset(
        specs=[dg.AssetSpec("a"), dg.AssetSpec("b")],
        check_specs=[
            dg.AssetCheckSpec("check1", asset="a"),
            dg.AssetCheckSpec("check2", asset="b"),
        ],
        can_subset=True,
    )
    def always_yields_b_check(context: AssetExecutionContext):
        for _asset in context.selected_asset_keys:
            yield dg.AssetMaterialization(asset_key=_asset)
        yield dg.AssetCheckResult(check_name="check1", asset_key=dg.AssetKey("a"), passed=True)

    result = dg.materialize_to_memory(
        [always_yields_b_check],
        selection="b",  # so b and b's check are selected
    )
    assert result.success
    evals = result.get_asset_check_evaluations()
    assert len(evals) == 1
    assert evals[0].check_name == "check1"
    assert evals[0].asset_key == dg.AssetKey("a")


def test_asset_hooks():
    @dg.success_hook
    def my_hook(context: HookContext):
        context.log.info("my_hook")

    @dg.asset(hooks={my_hook})
    def my_asset(context: AssetExecutionContext):
        context.log.info("my_asset")

    @dg.asset
    def my_other_asset(context: AssetExecutionContext):
        context.log.info("my_other_asset")

    job = dg.define_asset_job(
        name="my_job",
        selection=[my_asset, my_other_asset],
    )

    defs = dg.Definitions(
        assets=[my_asset, my_other_asset],
        jobs=[job],
    )

    result = defs.get_job_def("my_job").execute_in_process()
    hook_completed = [
        event for event in result.all_events if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_completed) == 1
    assert hook_completed[0].step_key == "my_asset"


def test_multi_asset_hooks():
    @dg.success_hook
    def success_hook_fn(context: HookContext):
        context.log.info(f"Success hook triggered for {context.op.name}")

    @dg.failure_hook
    def failure_hook_fn(context: HookContext):
        context.log.info(f"Failure hook triggered for {context.op.name}")

    @dg.multi_asset(
        outs={
            "asset1": dg.AssetOut(),
            "asset2": dg.AssetOut(),
        },
        hooks={success_hook_fn, failure_hook_fn},
    )
    def my_multi_asset(context: AssetExecutionContext):
        return 1, 2

    # Materialize the multi-asset and verify hooks
    result = dg.materialize([my_multi_asset])
    assert result.success

    # Verify that the success hook was triggered
    hook_completed = [
        event.event_type
        for event in result.all_events
        if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_completed) == 1
    hook_skipped = [
        event.event_type for event in result.all_events if "HOOK_SKIPPED" == event.event_type_value
    ]
    assert len(hook_skipped) == 1


def test_graph_asset_hooks():
    @dg.success_hook
    def my_hook(context: HookContext):
        context.log.info("my_hook")

    @dg.op
    def fetch_files_from_slack():
        pass

    @dg.op
    def store_files(files) -> None:
        pass

    @graph_asset(hooks={my_hook})
    def my_graph_asset():
        return store_files(fetch_files_from_slack())

    job = dg.define_asset_job(
        name="my_job",
        selection=[my_graph_asset],
    )

    defs = dg.Definitions(
        assets=[my_graph_asset],
        jobs=[job],
    )

    result = defs.get_job_def("my_job").execute_in_process()
    hook_completed = [
        event for event in result.all_events if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_completed) == 2
    assert hook_completed[0].step_key == "my_graph_asset.fetch_files_from_slack"
    assert hook_completed[1].step_key == "my_graph_asset.store_files"


def test_hook_requirements_forwarding():
    @dg.success_hook(required_resource_keys={"my_resource"})
    def hook_with_requirements(context: HookContext):
        assert context.resources.my_resource == "blah"
        context.log.info("Hook executed with required resources")

    @dg.asset(hooks={hook_with_requirements})
    def asset_with_hook(context):
        context.log.info("Asset executed")
        return 1

    # Verify that the resource requirements from the hook are included in the asset's requirements
    assert "my_resource" in asset_with_hook.required_resource_keys

    # Execute the asset with the required resources
    result = dg.materialize(
        [asset_with_hook],
        resources={"my_resource": ResourceDefinition.hardcoded_resource("blah")},
    )

    # Verify that the hook was executed
    hook_events = [
        event for event in result.all_events if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_events) == 1


def test_complex_graph_structure_hooks():
    # Create resources for testing requirements
    @dg.resource
    def job_resource(_):
        return "job_resource"

    @dg.resource
    def asset_resource(_):
        return "asset_resource"

    @dg.resource
    def op_resource(_):
        return "op_resource"

    # Create hooks with different resource requirements
    @dg.success_hook(required_resource_keys={"job_resource"})
    def job_hook(context: HookContext):
        assert context.resources.job_resource == "job_resource"
        context.log.info("Job hook executed")

    @dg.success_hook(required_resource_keys={"asset_resource"})
    def asset_hook(context: HookContext):
        assert context.resources.asset_resource == "asset_resource"
        context.log.info("Asset hook executed")

    @dg.success_hook(required_resource_keys={"op_resource"})
    def op_hook(context: HookContext):
        assert context.resources.op_resource == "op_resource"
        context.log.info("Op hook executed")

    # Create a regular asset with a hook
    @dg.asset(hooks={asset_hook})
    def regular_asset(context):
        context.log.info("Regular asset executed")
        return 1

    # Create a multi-asset with no hooks
    @dg.multi_asset(
        outs={
            "multi_out1": dg.AssetOut(),
            "multi_out2": dg.AssetOut(),
        }
    )
    def multi_asset_no_hooks(context):
        context.log.info("Multi-asset executed")
        return 1, 2

    # Create a graph asset where one of the ops has a hook
    @dg.op
    def first_op():
        return 1

    @dg.op
    def middle_op(value):
        return value + 1

    @dg.op
    def last_op(value):
        return value + 1

    @dg.op
    def sum_op(a, b):
        return a + b

    @graph_asset(
        ins={
            "regular_asset": dg.AssetIn("regular_asset"),
            "multi_out1": dg.AssetIn("multi_out1"),
        },
    )
    def complex_graph_asset(regular_asset, multi_out1):
        # Use inputs from other assets
        middle_result = middle_op.with_hooks({op_hook})(
            sum_op(first_op(), sum_op(regular_asset, multi_out1))
        )
        return last_op(middle_result)

    # Create a job with a hook
    job = dg.define_asset_job(
        name="complex_job",
        selection=[regular_asset, multi_asset_no_hooks, complex_graph_asset],
        hooks={job_hook},
    )

    # Create definitions
    defs = dg.Definitions(
        assets=[regular_asset, multi_asset_no_hooks, complex_graph_asset],
        jobs=[job],
        resources={
            "job_resource": job_resource,
            "asset_resource": asset_resource,
            "op_resource": op_resource,
        },
    )

    # Execute the job
    result = defs.get_job_def("complex_job").execute_in_process()
    assert result.success

    # Extract hook events
    hook_events = [
        event for event in result.all_events if "HOOK_COMPLETED" == event.event_type_value
    ]

    # Check that all hooks were executed
    job_hook_events = [e for e in hook_events if "job_hook" in str(e.message)]
    asset_hook_events = [e for e in hook_events if "asset_hook" in str(e.message)]
    op_hook_events = [e for e in hook_events if "op_hook" in str(e.message)]

    # Job hook should be applied to all steps
    # 7 ops => regular_asset, multi_asset_no_hooks,
    #    first_op, middle_op, last_op, sum_op (x2)

    step_keys_job_hook = [e.step_key for e in job_hook_events]
    assert set(step_keys_job_hook) == {
        "regular_asset",
        "multi_asset_no_hooks",
        "complex_graph_asset.first_op",
        "complex_graph_asset.middle_op",
        "complex_graph_asset.last_op",
        "complex_graph_asset.sum_op",
        "complex_graph_asset.sum_op_2",
    }

    # Asset hook should be applied only to the regular_asset
    assert len(asset_hook_events) == 1
    assert "regular_asset" == asset_hook_events[0].step_key

    # Op hook should be applied only to the middle_op in the graph asset
    assert len(op_hook_events) == 1
    assert "complex_graph_asset.middle_op" == op_hook_events[0].step_key

    # Verify the resource requirements were correctly propagated
    # Check if asset_resource is included in regular_asset's required_resource_keys
    assert "asset_resource" in regular_asset.required_resource_keys

    # Check if op_resource is included in complex_graph_asset's required_resource_keys
    assert "op_resource" in complex_graph_asset.required_resource_keys


@pytest.fixture
def hook_testing_utils():
    """Fixture providing utilities for hook testing."""
    executed_hooks = []

    # Helper function to log execution
    def log_execution(name):
        return name

    # Define hooks for testing
    @dg.success_hook
    def track_hook_execution(context: HookContext):
        executed_hooks.append(f"{context.step_key}_hook")
        context.log.info(f"Hook executed for {context.step_key}")

    @dg.success_hook
    def another_hook(context: HookContext):
        executed_hooks.append(f"{context.step_key}_another_hook")
        context.log.info(f"Another hook executed for {context.step_key}")

    @dg.success_hook
    def third_hook(context: HookContext):
        executed_hooks.append(f"{context.step_key}_third_hook")
        context.log.info(f"Third hook executed for {context.step_key}")

    def clear_tracking():
        executed_hooks.clear()

    return {
        "executed_hooks": executed_hooks,
        "log_execution": log_execution,
        "track_hook_execution": track_hook_execution,
        "another_hook": another_hook,
        "third_hook": third_hook,
        "clear_tracking": clear_tracking,
    }


def test_linear_chain_hooks(hook_testing_utils):
    """Test linear chain dependency pattern with hooks: A → B → C → D."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]

    @dg.asset(hooks={track_hook_execution})
    def linear_a():
        return log_execution("linear_a")

    @dg.asset(deps=["linear_a"])
    def linear_b():
        return log_execution("linear_b")

    @dg.asset(deps=["linear_b"], hooks={track_hook_execution, another_hook})
    def linear_c():
        return log_execution("linear_c")

    @dg.asset(deps=["linear_c"])
    def linear_d():
        return log_execution("linear_d")

    # Define job
    linear_job = dg.define_asset_job(
        "linear_job", selection=[linear_a, linear_b, linear_c, linear_d]
    )
    defs = dg.Definitions(assets=[linear_a, linear_b, linear_c, linear_d], jobs=[linear_job])

    # Execute and verify
    result = defs.get_job_def("linear_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "linear_a_hook",
        "linear_c_hook",
        "linear_c_another_hook",
    }


def test_diamond_pattern_hooks(hook_testing_utils):
    """Test diamond dependency pattern with hooks: A → (B, C) → D."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset
    def diamond_a():
        return log_execution("diamond_a")

    @dg.asset(deps=["diamond_a"], hooks={track_hook_execution})
    def diamond_b():
        return log_execution("diamond_b")

    @dg.asset(deps=["diamond_a"], hooks={another_hook})
    def diamond_c():
        return log_execution("diamond_c")

    @dg.asset(deps=["diamond_b", "diamond_c"], hooks={third_hook})
    def diamond_d():
        return log_execution("diamond_d")

    # Define job
    diamond_job = dg.define_asset_job(
        "diamond_job", selection=[diamond_a, diamond_b, diamond_c, diamond_d]
    )
    defs = dg.Definitions(assets=[diamond_a, diamond_b, diamond_c, diamond_d], jobs=[diamond_job])

    # Execute and verify
    result = defs.get_job_def("diamond_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "diamond_b_hook",
        "diamond_c_another_hook",
        "diamond_d_third_hook",
    }


def test_fan_out_hooks(hook_testing_utils):
    """Test fan-out dependency pattern with hooks: A → (B, C, D, E)."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def fan_out_a():
        return log_execution("fan_out_a")

    @dg.asset(deps=["fan_out_a"])
    def fan_out_b():
        return log_execution("fan_out_b")

    @dg.asset(deps=["fan_out_a"], hooks={another_hook})
    def fan_out_c():
        return log_execution("fan_out_c")

    @dg.asset(deps=["fan_out_a"])
    def fan_out_d():
        return log_execution("fan_out_d")

    @dg.asset(deps=["fan_out_a"], hooks={third_hook})
    def fan_out_e():
        return log_execution("fan_out_e")

    # Define job
    fan_out_job = dg.define_asset_job(
        "fan_out_job", selection=[fan_out_a, fan_out_b, fan_out_c, fan_out_d, fan_out_e]
    )
    defs = dg.Definitions(
        assets=[fan_out_a, fan_out_b, fan_out_c, fan_out_d, fan_out_e],
        jobs=[fan_out_job],
    )

    # Execute and verify
    result = defs.get_job_def("fan_out_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "fan_out_a_hook",
        "fan_out_c_another_hook",
        "fan_out_e_third_hook",
    }


def test_fan_in_hooks(hook_testing_utils):
    """Test fan-in dependency pattern with hooks: (A, B, C, D) → E."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def fan_in_a():
        return log_execution("fan_in_a")

    @dg.asset
    def fan_in_b():
        return log_execution("fan_in_b")

    @dg.asset(hooks={another_hook})
    def fan_in_c():
        return log_execution("fan_in_c")

    @dg.asset
    def fan_in_d():
        return log_execution("fan_in_d")

    @dg.asset(deps=["fan_in_a", "fan_in_b", "fan_in_c", "fan_in_d"], hooks={third_hook})
    def fan_in_e():
        return log_execution("fan_in_e")

    # Define job
    fan_in_job = dg.define_asset_job(
        "fan_in_job", selection=[fan_in_a, fan_in_b, fan_in_c, fan_in_d, fan_in_e]
    )
    defs = dg.Definitions(
        assets=[fan_in_a, fan_in_b, fan_in_c, fan_in_d, fan_in_e],
        jobs=[fan_in_job],
    )

    # Execute and verify
    result = defs.get_job_def("fan_in_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "fan_in_a_hook",
        "fan_in_c_another_hook",
        "fan_in_e_third_hook",
    }


def test_sibling_chain_hooks(hook_testing_utils):
    """Test sibling chain dependency pattern with hooks: A → B → C, A → D → E."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def sibling_a():
        return log_execution("sibling_a")

    @dg.asset(deps=["sibling_a"])
    def sibling_b():
        return log_execution("sibling_b")

    @dg.asset(deps=["sibling_b"], hooks={another_hook})
    def sibling_c():
        return log_execution("sibling_c")

    @dg.asset(deps=["sibling_a"], hooks={third_hook})
    def sibling_d():
        return log_execution("sibling_d")

    @dg.asset(deps=["sibling_d"])
    def sibling_e():
        return log_execution("sibling_e")

    # Define job
    sibling_job = dg.define_asset_job(
        "sibling_job", selection=[sibling_a, sibling_b, sibling_c, sibling_d, sibling_e]
    )
    defs = dg.Definitions(
        assets=[sibling_a, sibling_b, sibling_c, sibling_d, sibling_e],
        jobs=[sibling_job],
    )

    # Execute and verify
    result = defs.get_job_def("sibling_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "sibling_a_hook",
        "sibling_c_another_hook",
        "sibling_d_third_hook",
    }


def test_skip_level_hooks(hook_testing_utils):
    """Test skip-level dependency pattern with hooks: A → B → C, A → C."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def skip_a():
        return log_execution("skip_a")

    @dg.asset(deps=["skip_a"], hooks={another_hook})
    def skip_b():
        return log_execution("skip_b")

    @dg.asset(deps=["skip_a", "skip_b"], hooks={third_hook})
    def skip_c():
        return log_execution("skip_c")

    # Define job
    skip_job = dg.define_asset_job("skip_job", selection=[skip_a, skip_b, skip_c])
    defs = dg.Definitions(assets=[skip_a, skip_b, skip_c], jobs=[skip_job])

    # Execute and verify
    result = defs.get_job_def("skip_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "skip_a_hook",
        "skip_b_another_hook",
        "skip_c_third_hook",
    }


def test_complex_dag_hooks(hook_testing_utils):
    """Test complex DAG dependency pattern with hooks."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def complex_a():
        return log_execution("complex_a")

    @dg.asset(deps=["complex_a"])
    def complex_b():
        return log_execution("complex_b")

    @dg.asset(deps=["complex_a"], hooks={another_hook})
    def complex_c():
        return log_execution("complex_c")

    @dg.asset(deps=["complex_b", "complex_c"])
    def complex_d():
        return log_execution("complex_d")

    @dg.asset(deps=["complex_c"], hooks={third_hook})
    def complex_e():
        return log_execution("complex_e")

    @dg.asset(deps=["complex_d", "complex_e"])
    def complex_f():
        return log_execution("complex_f")

    # Define job
    complex_job = dg.define_asset_job(
        "complex_job", selection=[complex_a, complex_b, complex_c, complex_d, complex_e, complex_f]
    )
    defs = dg.Definitions(
        assets=[complex_a, complex_b, complex_c, complex_d, complex_e, complex_f],
        jobs=[complex_job],
    )

    # Execute and verify
    result = defs.get_job_def("complex_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "complex_a_hook",
        "complex_c_another_hook",
        "complex_e_third_hook",
    }


def test_isolated_assets_hooks(hook_testing_utils):
    """Test isolated assets with hooks: X, Y (no dependencies)."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def isolated_x():
        return log_execution("isolated_x")

    @dg.asset(hooks={another_hook})
    def isolated_y():
        return log_execution("isolated_y")

    # Define job
    isolated_job = dg.define_asset_job("isolated_job", selection=[isolated_x, isolated_y])
    defs = dg.Definitions(assets=[isolated_x, isolated_y], jobs=[isolated_job])

    # Execute and verify
    result = defs.get_job_def("isolated_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 2
    assert set(executed_hooks) == {"isolated_x_hook", "isolated_y_another_hook"}


def test_layered_dependencies_hooks(hook_testing_utils):
    """Test layered dependency pattern with hooks: Layer1 → Layer2 → Layer3."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    # Layer 1
    @dg.asset(hooks={track_hook_execution})
    def layer1_a():
        return log_execution("layer1_a")

    @dg.asset
    def layer1_b():
        return log_execution("layer1_b")

    # Layer 2
    @dg.asset(deps=["layer1_a"])
    def layer2_a():
        return log_execution("layer2_a")

    @dg.asset(deps=["layer1_a", "layer1_b"], hooks={another_hook})
    def layer2_b():
        return log_execution("layer2_b")

    @dg.asset(deps=["layer1_b"])
    def layer2_c():
        return log_execution("layer2_c")

    # Layer 3
    @dg.asset(deps=["layer2_a", "layer2_b"], hooks={third_hook})
    def layer3_a():
        return log_execution("layer3_a")

    @dg.asset(deps=["layer2_b", "layer2_c"])
    def layer3_b():
        return log_execution("layer3_b")

    # Define job
    layer_job = dg.define_asset_job(
        "layer_job",
        selection=[layer1_a, layer1_b, layer2_a, layer2_b, layer2_c, layer3_a, layer3_b],
    )
    defs = dg.Definitions(
        assets=[layer1_a, layer1_b, layer2_a, layer2_b, layer2_c, layer3_a, layer3_b],
        jobs=[layer_job],
    )

    # Execute and verify
    result = defs.get_job_def("layer_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 3
    assert set(executed_hooks) == {
        "layer1_a_hook",
        "layer2_b_another_hook",
        "layer3_a_third_hook",
    }


def test_cyclic_dependencies_hooks(hook_testing_utils):
    """Test cyclic dependencies within layers with hooks."""
    log_execution = hook_testing_utils["log_execution"]
    track_hook_execution = hook_testing_utils["track_hook_execution"]
    another_hook = hook_testing_utils["another_hook"]
    third_hook = hook_testing_utils["third_hook"]
    executed_hooks = hook_testing_utils["executed_hooks"]
    hook_testing_utils["clear_tracking"]()

    @dg.asset(hooks={track_hook_execution})
    def cycle_layer1_a():
        return log_execution("cycle_layer1_a")

    @dg.asset(hooks={another_hook})
    def cycle_layer1_b():
        return log_execution("cycle_layer1_b")

    @dg.asset(deps=["cycle_layer1_a", "cycle_layer1_b"])
    def cycle_layer2_a():
        return log_execution("cycle_layer2_a")

    @dg.asset(deps=["cycle_layer1_a"], hooks={another_hook})
    def cycle_layer2_b():
        return log_execution("cycle_layer2_b")

    @dg.asset(deps=["cycle_layer1_b"])
    def cycle_layer2_c():
        return log_execution("cycle_layer2_c")

    @dg.asset(deps=["cycle_layer2_a", "cycle_layer2_b"])
    def cycle_layer3_a():
        return log_execution("cycle_layer3_a")

    @dg.asset(deps=["cycle_layer2_a", "cycle_layer2_c"], hooks={third_hook})
    def cycle_layer3_b():
        return log_execution("cycle_layer3_b")

    @dg.asset(deps=["cycle_layer2_b", "cycle_layer2_c"])
    def cycle_layer3_c():
        return log_execution("cycle_layer3_c")

    @dg.asset(deps=["cycle_layer3_a", "cycle_layer3_b", "cycle_layer3_c"])
    def cycle_output():
        return log_execution("cycle_output")

    # Define job
    cycle_job = dg.define_asset_job(
        "cycle_job",
        selection=[
            cycle_layer1_a,
            cycle_layer1_b,
            cycle_layer2_a,
            cycle_layer2_b,
            cycle_layer2_c,
            cycle_layer3_a,
            cycle_layer3_b,
            cycle_layer3_c,
            cycle_output,
        ],
    )
    defs = dg.Definitions(
        assets=[
            cycle_layer1_a,
            cycle_layer1_b,
            cycle_layer2_a,
            cycle_layer2_b,
            cycle_layer2_c,
            cycle_layer3_a,
            cycle_layer3_b,
            cycle_layer3_c,
            cycle_output,
        ],
        jobs=[cycle_job],
    )

    # Execute and verify
    result = defs.get_job_def("cycle_job").execute_in_process()
    assert result.success
    assert len(executed_hooks) == 4
    assert set(executed_hooks) == {
        "cycle_layer1_a_hook",
        "cycle_layer1_b_another_hook",
        "cycle_layer2_b_another_hook",
        "cycle_layer3_b_third_hook",
    }


def test_metadata_update():
    @dg.asset(metadata={"foo": "bar", "four": 4})
    def single(): ...

    assert single.metadata_by_key[single.key]["foo"] == "bar"  # gets normalized later?
    assert single.metadata_by_key[single.key]["four"] == 4

    updated = single.with_attributes(
        metadata_by_key={
            single.key: {
                **single.metadata_by_key[single.key],
                "foo": "baz",
            }
        }
    )
    assert updated.metadata_by_key[updated.key]["foo"] == "baz"
    assert updated.metadata_by_key[updated.key]["four"] == 4

    # cant blank out metadata for this condition
    # * @asset creates an OpDefinition with the metadata set on the output
    # * The AssetsDefinition constructor merges the output metadata with the spec metadata
    tried_to_blank = single.with_attributes(metadata_by_key={single.key: {}})
    # so here we still get back the metadata from the op def output node
    assert tried_to_blank.metadata_by_key[tried_to_blank.key] == {"foo": "bar", "four": 4}

    asset_a = dg.AssetSpec("a", metadata={"a": "foo"})
    asset_b = dg.AssetSpec("b", metadata={"b": 3})

    @dg.multi_asset(specs=[asset_a, asset_b])
    def multi(): ...

    assert multi.metadata_by_key[asset_a.key]["a"] == "foo"
    assert multi.metadata_by_key[asset_b.key]["b"] == 3

    updated = multi.with_attributes(
        metadata_by_key={
            asset_a.key: {
                **multi.metadata_by_key[asset_a.key],
                "a": "bar",
            }
        }
    )
    assert updated.metadata_by_key[asset_a.key]["a"] == "bar"

    # same as above
    tried_to_blank = multi.with_attributes(metadata_by_key={asset_a.key: {}, asset_b.key: {}})
    assert tried_to_blank.metadata_by_key == {asset_a.key: {"a": "foo"}, asset_b.key: {"b": 3}}

    @dg.asset_check(asset=single, metadata={"foo": "bar"})
    def my_check():
        return dg.AssetCheckResult(passed=True)

    assert next(iter(my_check.check_specs)).metadata["foo"] == "bar"

    blanked = my_check.with_attributes(metadata_by_key={my_check.check_key: {}})
    assert next(iter(blanked.check_specs)).metadata == {}

    updated = my_check.with_attributes(metadata_by_key={my_check.check_key: {"foo": "baz"}})
    assert next(iter(updated.check_specs)).metadata["foo"] == "baz"
