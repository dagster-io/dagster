import os
import pickle
import re
from tempfile import TemporaryDirectory

import dagster as dg
import pytest
from dagster import AssetExecutionContext, MetadataValue, ResourceDefinition
from dagster._core.test_utils import ignore_warning, raise_exception_on_warnings


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def test_basic_materialize():
    @dg.asset
    def the_asset():
        return 5

    # Verify that result of materialize was persisted
    with TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(temp_dir=temp_dir) as instance:
            result = dg.materialize([the_asset], instance=instance)
            assert result.success
            assert result.asset_materializations_for_node("the_asset")[0].metadata[
                "path"
            ] == MetadataValue.path(os.path.join(temp_dir, "storage", "the_asset"))


def test_materialize_config():
    @dg.asset(config_schema={"foo_str": str})
    def the_asset_reqs_config(context):
        assert context.op_execution_context.op_config["foo_str"] == "foo"

    with dg.instance_for_test() as instance:
        assert dg.materialize(
            [the_asset_reqs_config],
            run_config={"ops": {"the_asset_reqs_config": {"config": {"foo_str": "foo"}}}},
            instance=instance,
        ).success


def test_materialize_bad_config():
    @dg.asset(config_schema={"foo_str": str})
    def the_asset_reqs_config(context):
        assert context.op_execution_context.op_config["foo_str"] == "foo"

    with dg.instance_for_test() as instance:
        with pytest.raises(dg.DagsterInvalidConfigError, match="Error in config for job"):
            dg.materialize(
                [the_asset_reqs_config],
                run_config={"ops": {"the_asset_reqs_config": {"config": {"bad": "foo"}}}},
                instance=instance,
            )


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_materialize_resources():
    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("blah")})
    def the_asset(context):
        assert context.resources.foo == "blah"

    with dg.instance_for_test() as instance:
        assert dg.materialize([the_asset], instance=instance).success


def test_materialize_resources_not_satisfied():
    @dg.asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == "blah"

    with dg.instance_for_test() as instance:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match="resource with key 'foo' required by op 'the_asset' was not provided",
        ):
            dg.materialize([the_asset], instance=instance)

        assert dg.materialize(
            dg.with_resources([the_asset], {"foo": ResourceDefinition.hardcoded_resource("blah")}),
            instance=instance,
        ).success


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_materialize_conflicting_resources():
    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def first():
        pass

    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")})
    def second():
        pass

    with dg.instance_for_test() as instance:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match=(
                r"Conflicting versions of resource with key 'foo' were provided to different assets."
            ),
        ):
            dg.materialize([first, second], instance=instance)


@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_materialize_source_assets():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def the_manager():
        return MyIOManager()

    the_source = dg.SourceAsset(key=dg.AssetKey(["the_source"]), io_manager_def=the_manager)

    @dg.asset
    def the_asset(the_source):
        return the_source + 1

    with dg.instance_for_test() as instance:
        result = dg.materialize([the_asset, the_source], instance=instance)
        assert result.success
        assert result.output_for_node("the_asset") == 6


def test_materialize_asset_specs():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    the_source = dg.AssetSpec(key=dg.AssetKey(["the_source"])).with_io_manager_key("my_io_manager")

    @dg.asset
    def the_asset(the_source):
        return the_source + 1

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [the_asset, the_source], instance=instance, resources={"my_io_manager": MyIOManager()}
        )
        assert result.success
        assert result.output_for_node("the_asset") == 6


def test_materialize_asset_specs_conflicting_key():
    the_source = dg.AssetSpec(key=dg.AssetKey(["the_source"]))

    @dg.asset(key="the_source")
    def the_asset(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape("Duplicate asset key: AssetKey(['the_source'])"),
    ):
        dg.materialize([the_asset, the_source])


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_materialize_source_asset_conflicts():
    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def the_asset():
        pass

    the_source = dg.SourceAsset(
        key=dg.AssetKey(["the_source"]),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")},
    )

    with dg.instance_for_test() as instance:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match=(
                r"Conflicting versions of resource with key 'foo' were provided to different assets."
            ),
        ):
            dg.materialize([the_asset, the_source], instance=instance)


def test_materialize_no_assets():
    with dg.instance_for_test() as instance:
        assert dg.materialize([], instance=instance).success


def test_materialize_graph_backed_asset():
    @dg.asset
    def a():
        return "a"

    @dg.asset
    def b():
        return "b"

    @dg.op
    def double_string(s):
        return s * 2

    @dg.op
    def combine_strings(s1, s2):
        return s1 + s2

    @dg.graph
    def create_cool_thing(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        return combine_strings(da, db)

    cool_thing_asset = dg.AssetsDefinition(
        keys_by_input_name={"a": dg.AssetKey("a"), "b": dg.AssetKey("b")},
        keys_by_output_name={"result": dg.AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )

    with dg.instance_for_test() as instance:
        result = dg.materialize([cool_thing_asset, a, b], instance=instance)
        assert result.success
        assert result.output_for_node("create_cool_thing.combine_strings") == "aaaabb"


def test_materialize_multi_asset():
    @dg.op
    def upstream_op():
        return "foo"

    @dg.op(out={"o1": dg.Out(), "o2": dg.Out()})
    def two_outputs(upstream_op):
        o1 = upstream_op
        o2 = o1 + "bar"
        return o1, o2

    @dg.graph(out={"o1": dg.GraphOut(), "o2": dg.GraphOut()})
    def thing():
        o1, o2 = two_outputs(upstream_op())
        return (o1, o2)

    thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("thing"), "o2": dg.AssetKey("thing_2")},
        node_def=thing,
        asset_deps={dg.AssetKey("thing"): set(), dg.AssetKey("thing_2"): {dg.AssetKey("thing")}},
    )

    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": dg.AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {dg.AssetKey("my_other_out_name")},
            "my_other_out_name": {dg.AssetKey("thing")},
        },
    )
    def multi_asset_with_internal_deps(thing):
        yield dg.Output(2, "my_other_out_name")
        yield dg.Output(1, "my_out_name")

    with dg.instance_for_test() as instance:
        result = dg.materialize([thing_asset, multi_asset_with_internal_deps], instance=instance)
        assert result.success
        assert result.output_for_node("multi_asset_with_internal_deps", "my_out_name") == 1
        assert result.output_for_node("multi_asset_with_internal_deps", "my_other_out_name") == 2


def test_materialize_tags():
    @dg.asset
    def the_asset(context):
        assert context.run.tags.get("key1") == "value1"

    with dg.instance_for_test() as instance:
        result = dg.materialize([the_asset], instance=instance, tags={"key1": "value1"})
        assert result.success
        assert result.dagster_run.tags == {"key1": "value1"}


def test_materialize_partition_key():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def the_asset(context: AssetExecutionContext):
        assert context.partition_key == "2022-02-02"

    with dg.instance_for_test() as instance:
        result = dg.materialize([the_asset], partition_key="2022-02-02", instance=instance)
        assert result.success


def test_materialize_provided_resources():
    @dg.asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == 5

    @dg.resource(required_resource_keys={"bar"})
    def foo_resource(init_context):
        return init_context.resources.bar + 1

    result = dg.materialize(
        [the_asset], resources={"foo": foo_resource, "bar": 4, "io_manager": dg.mem_io_manager}
    )
    assert result.success
    assert result.asset_materializations_for_node("the_asset")[0].metadata == {}


def test_conditional_materialize():
    should_materialize = True

    @dg.asset(output_required=False)
    def the_asset():
        if should_materialize:
            yield dg.Output(5)

    @dg.asset
    def downstream(the_asset):
        if the_asset:
            return the_asset + 1
        else:
            # if we get here then the_asset is None and downstream execution was not halted
            assert False

    # Verify that result of materialize was persisted
    with TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(temp_dir=temp_dir) as instance:
            result = dg.materialize([the_asset, downstream], instance=instance)
            assert result.success

            assert result.asset_materializations_for_node("the_asset")[0].metadata[
                "path"
            ] == MetadataValue.path(os.path.join(temp_dir, "storage", "the_asset"))
            with open(os.path.join(temp_dir, "storage", "the_asset"), "rb") as f:
                assert pickle.load(f) == 5

            assert result.asset_materializations_for_node("downstream")[0].metadata[
                "path"
            ] == MetadataValue.path(os.path.join(temp_dir, "storage", "downstream"))
            with open(os.path.join(temp_dir, "storage", "downstream"), "rb") as f:
                assert pickle.load(f) == 6

            should_materialize = False

            result = dg.materialize([the_asset, downstream], instance=instance)
            assert result.success

            assert len(result.asset_materializations_for_node("the_asset")) == 0
            with open(os.path.join(temp_dir, "storage", "the_asset"), "rb") as f:
                assert pickle.load(f) == 5

            assert len(result.asset_materializations_for_node("downstream")) == 0
            with open(os.path.join(temp_dir, "storage", "downstream"), "rb") as f:
                assert pickle.load(f) == 6


def test_raise_on_error():
    @dg.asset
    def asset1():
        raise ValueError()

    with dg.instance_for_test() as instance:
        assert not dg.materialize([asset1], raise_on_error=False, instance=instance).success


def test_selection():
    @dg.asset
    def upstream(): ...

    @dg.asset
    def downstream(upstream): ...

    assets = [upstream, downstream]

    with TemporaryDirectory() as temp_dir:
        with dg.instance_for_test(temp_dir=temp_dir) as instance:
            result1 = dg.materialize(assets, instance=instance, selection=[upstream])
            assert result1.success
            materialization_events = result1.get_asset_materialization_events()
            assert len(materialization_events) == 1
            assert materialization_events[0].materialization.asset_key == dg.AssetKey("upstream")

            result2 = dg.materialize(assets, instance=instance, selection=[downstream])
            assert result2.success
            materialization_events = result2.get_asset_materialization_events()
            assert len(materialization_events) == 1
            assert materialization_events[0].materialization.asset_key == dg.AssetKey("downstream")
