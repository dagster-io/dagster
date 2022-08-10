import os
import pickle
import warnings
from tempfile import TemporaryDirectory

import pytest

from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    GraphOut,
    IOManager,
    MetadataValue,
    Out,
    Output,
    ResourceDefinition,
    SourceAsset,
    asset,
    graph,
    io_manager,
    materialize,
    mem_io_manager,
    multi_asset,
    op,
    resource,
    with_resources,
)
from dagster._core.test_utils import instance_for_test


@pytest.fixture(autouse=True)
def check_experimental_warnings():
    with warnings.catch_warnings(record=True) as record:
        yield

        for w in record:
            # Expect experimental warnings to be thrown for direct
            # resource_defs and io_manager_def arguments.
            if "resource_defs" in w.message.args[0] or "io_manager_def" in w.message.args[0]:
                continue
            assert False, f"Unexpected warning: {w.message.args[0]}"


def test_basic_materialize():
    @asset
    def the_asset():
        return 5

    # Verify that result of materialize was persisted
    with TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            result = materialize([the_asset], instance=instance)
            assert result.success
            assert result.asset_materializations_for_node("the_asset")[0].metadata_entries[
                0
            ].value == MetadataValue.path(os.path.join(temp_dir, "storage", "the_asset"))


def test_materialize_config():
    @asset(config_schema={"foo_str": str})
    def the_asset_reqs_config(context):
        assert context.op_config["foo_str"] == "foo"

    with instance_for_test() as instance:
        assert materialize(
            [the_asset_reqs_config],
            run_config={"ops": {"the_asset_reqs_config": {"config": {"foo_str": "foo"}}}},
            instance=instance,
        ).success


def test_materialize_bad_config():
    @asset(config_schema={"foo_str": str})
    def the_asset_reqs_config(context):
        assert context.op_config["foo_str"] == "foo"

    with instance_for_test() as instance:
        with pytest.raises(DagsterInvalidConfigError, match="Error in config for job"):
            materialize(
                [the_asset_reqs_config],
                run_config={"ops": {"the_asset_reqs_config": {"config": {"bad": "foo"}}}},
                instance=instance,
            )


def test_materialize_resources():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("blah")})
    def the_asset(context):
        assert context.resources.foo == "blah"

    with instance_for_test() as instance:
        assert materialize([the_asset], instance=instance).success


def test_materialize_resources_not_satisfied():
    @asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == "blah"

    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match="resource with key 'foo' required by op 'the_asset' was not provided",
        ):
            materialize([the_asset], instance=instance)

        assert materialize(
            with_resources([the_asset], {"foo": ResourceDefinition.hardcoded_resource("blah")}),
            instance=instance,
        ).success


def test_materialize_conflicting_resources():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def first():
        pass

    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")})
    def second():
        pass

    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match="Conflicting versions of resource with key 'foo' were provided to different assets.",
        ):
            materialize([first, second], instance=instance)


def test_materialize_source_assets():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    the_source = SourceAsset(key=AssetKey(["the_source"]), io_manager_def=the_manager)

    @asset
    def the_asset(the_source):
        return the_source + 1

    with instance_for_test() as instance:
        result = materialize([the_asset, the_source], instance=instance)
        assert result.success
        assert result.output_for_node("the_asset") == 6


def test_materialize_source_asset_conflicts():
    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def the_asset():
        pass

    the_source = SourceAsset(
        key=AssetKey(["the_source"]),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")},
    )

    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match="Conflicting versions of resource with key 'foo' were provided to different assets.",
        ):
            materialize([the_asset, the_source], instance=instance)


def test_materialize_no_assets():
    with instance_for_test() as instance:
        assert materialize([], instance=instance).success


def test_materialize_graph_backed_asset():
    @asset
    def a():
        return "a"

    @asset
    def b():
        return "b"

    @op
    def double_string(s):
        return s * 2

    @op
    def combine_strings(s1, s2):
        return s1 + s2

    @graph
    def create_cool_thing(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        return combine_strings(da, db)

    cool_thing_asset = AssetsDefinition(
        keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        keys_by_output_name={"result": AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )

    with instance_for_test() as instance:
        result = materialize([cool_thing_asset, a, b], instance=instance)
        assert result.success
        assert result.output_for_node("create_cool_thing.combine_strings") == "aaaabb"


def test_materialize_multi_asset():
    @op
    def upstream_op():
        return "foo"

    @op(out={"o1": Out(), "o2": Out()})
    def two_outputs(upstream_op):
        o1 = upstream_op
        o2 = o1 + "bar"
        return o1, o2

    @graph(out={"o1": GraphOut(), "o2": GraphOut()})
    def thing():
        o1, o2 = two_outputs(upstream_op())
        return (o1, o2)

    thing_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("thing"), "o2": AssetKey("thing_2")},
        node_def=thing,
        asset_deps={AssetKey("thing"): set(), AssetKey("thing_2"): {AssetKey("thing")}},
    )

    @multi_asset(
        outs={
            "my_out_name": AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {AssetKey("my_other_out_name")},
            "my_other_out_name": {AssetKey("thing")},
        },
    )
    def multi_asset_with_internal_deps(thing):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    with instance_for_test() as instance:
        result = materialize([thing_asset, multi_asset_with_internal_deps], instance=instance)
        assert result.success
        assert result.output_for_node("multi_asset_with_internal_deps", "my_out_name") == 1
        assert result.output_for_node("multi_asset_with_internal_deps", "my_other_out_name") == 2


def test_materialize_partition_key():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def the_asset(context):
        assert context.asset_partition_key_for_output() == "2022-02-02"

    with instance_for_test() as instance:
        result = materialize([the_asset], partition_key="2022-02-02", instance=instance)
        assert result.success


def test_materialize_provided_resources():
    @asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == 5

    @resource(required_resource_keys={"bar"})
    def foo_resource(init_context):
        return init_context.resources.bar + 1

    result = materialize(
        [the_asset], resources={"foo": foo_resource, "bar": 4, "io_manager": mem_io_manager}
    )
    assert result.success
    assert result.asset_materializations_for_node("the_asset")[0].metadata_entries == []


def test_conditional_materialize():
    should_materialize = True

    @asset(always_materialize=False)
    def the_asset():
        if should_materialize:
            yield Output(5)

    @asset
    def downstream(the_asset):
        if the_asset:
            return the_asset + 1
        else:
            # if we get here then the_asset is None and downstream execution was not halted
            assert False

    # Verify that result of materialize was persisted
    with TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            result = materialize([the_asset, downstream], instance=instance)
            assert result.success

            assert result.asset_materializations_for_node("the_asset")[0].metadata_entries[
                0
            ].value == MetadataValue.path(os.path.join(temp_dir, "storage", "the_asset"))
            with open(os.path.join(temp_dir, "storage", "the_asset"), "rb") as f:
                assert pickle.load(f) == 5

            assert result.asset_materializations_for_node("downstream")[0].metadata_entries[
                0
            ].value == MetadataValue.path(os.path.join(temp_dir, "storage", "downstream"))
            with open(os.path.join(temp_dir, "storage", "downstream"), "rb") as f:
                assert pickle.load(f) == 6

            should_materialize = False

            result = materialize([the_asset, downstream], instance=instance)
            assert result.success

            assert len(result.asset_materializations_for_node("the_asset")) == 0
            with open(os.path.join(temp_dir, "storage", "the_asset"), "rb") as f:
                assert pickle.load(f) == 5

            assert len(result.asset_materializations_for_node("downstream")) == 0
            with open(os.path.join(temp_dir, "storage", "downstream"), "rb") as f:
                assert pickle.load(f) == 6
