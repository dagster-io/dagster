import pytest

from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterEventType,
    EventRecordsFilter,
    GraphOut,
    IOManager,
    IOManagerDefinition,
    Out,
    Output,
    ResourceDefinition,
    build_op_context,
    define_asset_job,
    graph,
    io_manager,
    materialize,
    materialize_to_memory,
    op,
    resource,
)
from dagster._check import CheckError
from dagster._core.definitions import AssetGroup, AssetIn, SourceAsset, asset, multi_asset
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.storage.mem_io_manager import InMemoryIOManager
from dagster._core.test_utils import instance_for_test


def test_with_replaced_asset_keys():
    @asset(ins={"input2": AssetIn(key_prefix="something_else")})
    def asset1(input1, input2):
        assert input1
        assert input2

    replaced = asset1.with_prefix_or_group(
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
        ("foo,bar,baz,in1,in2,in3,a,b,c,foo2,bar2,baz2", "a,b,c", 3, 3),
        ("foo,bar,baz", None, 0, 0),
        ("in1,a,b,c", "a,b,c", 3, 3),
        ("foo,in1,a,b,c,bar", "a,b,c", 3, 3),
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
    def abc_(context, in1, in2, in3):  # pylint: disable=unused-argument
        pass

    subbed = abc_.subset_for({AssetKey(key) for key in subset.split(",")})

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

    replaced = bar.with_prefix_or_group(
        output_asset_key_replacements={AssetKey(["bar"]): AssetKey(["baz"])}
    )
    assert replaced.group_names_by_key[AssetKey("baz")] == "foo"


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

    subset = ma.subset_for({AssetKey("b")})
    assert subset.group_names_by_key[AssetKey("b")] == "bar"


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
    def abc_(context, in1, in2, in3):  # pylint: disable=unused-argument
        pass

    replaced_1 = abc_.with_prefix_or_group(
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
        {AssetKey(["foo", "bar_in1"]), AssetKey("in3"), AssetKey(["foo", "foo_a"]), AssetKey("b")}
    )
    assert subbed_1.keys == {AssetKey(["foo", "foo_a"]), AssetKey("b")}

    replaced_2 = subbed_1.with_prefix_or_group(
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
        }
    )
    assert subbed_2.keys == {AssetKey(["again", "foo", "foo_a"])}


def test_fail_on_subset_for_nonsubsettable():
    @multi_asset(outs={"a": AssetOut(), "b": AssetOut(), "c": AssetOut()})
    def abc_(context, start):  # pylint: disable=unused-argument
        pass

    with pytest.raises(CheckError, match="can_subset=False"):
        abc_.subset_for({AssetKey("start"), AssetKey("a")})


def test_to_source_assets():
    @asset(metadata={"a": "b"}, io_manager_key="abc", description="blablabla")
    def my_asset():
        ...

    assert my_asset.to_source_assets() == [
        SourceAsset(
            AssetKey(["my_asset"]),
            metadata={"a": "b"},
            io_manager_key="abc",
            description="blablabla",
        )
    ]

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

    assert my_multi_asset.to_source_assets() == [
        SourceAsset(
            AssetKey(["my_asset_name"]),
            metadata={"a": "b"},
            io_manager_key="abc",
            description="blablabla",
        ),
        SourceAsset(
            AssetKey(["my_other_asset"]),
            metadata={"c": "d"},
            io_manager_key="def",
            description="ablablabl",
        ),
    ]


def test_coerced_asset_keys():
    @asset(ins={"input1": AssetIn(asset_key=["Asset", "1"])})
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

    result = AssetGroup([the_asset]).materialize()
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

    AssetGroup([the_asset, other_asset]).materialize()

    assert num_times[0] == 2

    the_asset_key = [key for key in io_manager_inst.values.keys() if key[1] == "the_asset"][0]
    assert io_manager_inst.values[the_asset_key] == 5

    other_asset_key = [key for key in io_manager_inst.values.keys() if key[1] == "other_asset"][0]
    assert io_manager_inst.values[other_asset_key] == 6


def test_asset_with_io_manager_key_only():
    io_manager_inst = InMemoryIOManager()

    @io_manager
    def the_io_manager():
        return io_manager_inst

    @asset(io_manager_key="the_key")
    def the_asset():
        return 5

    AssetGroup([the_asset], resource_defs={"the_key": the_io_manager}).materialize()

    assert list(io_manager_inst.values.values())[0] == 5


def test_asset_both_io_manager_args_provided():
    @io_manager
    def the_io_manager():
        pass

    with pytest.raises(
        CheckError,
        match="Both io_manager_key and io_manager_def were provided to `@asset` "
        "decorator. Please provide one or the other.",
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

    asset_reqs_resources(build_op_context(resources={"foo": "foo_resource", "bar": "bar_resource"}))

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
        asset_resource_overrides(build_op_context(resources={"foo": "override_foo"}))


def test_asset_invocation_resource_errors():
    @asset(resource_defs={"ignored": ResourceDefinition.hardcoded_resource("not_used")})
    def asset_doesnt_use_resources():
        pass

    asset_doesnt_use_resources()

    @asset(resource_defs={"used": ResourceDefinition.hardcoded_resource("foo")})
    def asset_uses_resources(context):
        assert context.resources.used == "foo"

    with pytest.raises(
        DagsterInvalidInvocationError,
        match='op "asset_uses_resources" has required resources, but no context was provided',
    ):
        asset_uses_resources(None)

    asset_uses_resources(build_op_context())

    @asset(required_resource_keys={"foo"})
    def required_key_not_provided(_):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'required_key_not_provided' was not provided.",
    ):
        required_key_not_provided(build_op_context())


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
            "key1": Out(asset_key=AssetKey("key1"), io_manager_key="foo"),
            "key2": Out(asset_key=AssetKey("key2"), io_manager_key="bar"),
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

    the_asset = AssetsDefinition.from_graph(
        graph_def=silly_graph,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
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

    the_asset = AssetsDefinition.from_op(
        op_def=foo,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey(["the", "asset"])},
        key_prefix=["this", "is", "a", "prefix"],
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


def get_step_keys_from_run(instance, run_result):
    engine_events = list(
        instance.get_event_records(EventRecordsFilter(DagsterEventType.ENGINE_EVENT))
    )
    metadata_entries = engine_events[
        0
    ].event_log_entry.dagster_event.engine_event_data.metadata_entries
    step_metadata = next(
        iter([metadata for metadata in metadata_entries if metadata.label == "step_keys"])
    )
    return eval(step_metadata.value.value)


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
        [
            AssetsDefinition.from_graph(my_graph, can_subset=True),
        ],
        [],
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(instance=instance, asset_selection=[AssetKey("one")])
        materialization_planned = list(
            instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        )
        assert len(materialization_planned) == 1
        step_keys = get_step_keys_from_run(instance, result)
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
        [
            AssetsDefinition.from_graph(graph_asset, can_subset=True),
        ],
        [],
    )

    with instance_for_test() as instance:
        result = asset_job.execute_in_process(instance=instance, asset_selection=[AssetKey("one")])
        materialization_planned = list(
            instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        )
        assert len(materialization_planned) == 1
        step_keys = get_step_keys_from_run(instance, result)
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

    asset_job = define_asset_job("yay").resolve(
        [
            upstream_1,
            upstream_2,
            AssetsDefinition.from_graph(my_graph, can_subset=True),
        ],
        [],
    )

    # test first "bar" alias
    with instance_for_test() as instance:
        result = asset_job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("one"), AssetKey("upstream_1"), AssetKey("upstream_2")],
        )
        materialization_planned = list(
            instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        )
        assert len(materialization_planned) == 3
        step_keys = get_step_keys_from_run(instance, result)
        assert set(step_keys) == set(["my_graph.bar_1", "upstream_1", "upstream_2"])

    # test second "bar" alias
    with instance_for_test() as instance:
        result = asset_job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("two"), AssetKey("upstream_1"), AssetKey("upstream_2")],
        )
        materialization_planned = list(
            instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        )
        assert len(materialization_planned) == 3
        step_keys = get_step_keys_from_run(instance, result)
        assert set(step_keys) == set(["my_graph.bar_2", "upstream_1", "upstream_2"])

    # test "baz" which uses both inputs
    with instance_for_test() as instance:
        result = asset_job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("three"), AssetKey("upstream_1"), AssetKey("upstream_2")],
        )
        materialization_planned = list(
            instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        )
        assert len(materialization_planned) == 3
        step_keys = get_step_keys_from_run(instance, result)
        assert set(step_keys) == set(["my_graph.baz", "upstream_1", "upstream_2"])
