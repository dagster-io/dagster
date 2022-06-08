import os
from tempfile import TemporaryDirectory

import pytest

from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
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
    multi_asset,
    op,
    with_resources,
)
from dagster.core.test_utils import instance_for_test


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

    assert materialize(
        [the_asset_reqs_config],
        run_config={"ops": {"the_asset_reqs_config": {"config": {"foo_str": "foo"}}}},
    ).success


def test_materialize_bad_config():
    @asset(config_schema={"foo_str": str})
    def the_asset_reqs_config(context):
        assert context.op_config["foo_str"] == "foo"

    with pytest.raises(DagsterInvalidConfigError, match="Error in config for job"):
        materialize(
            [the_asset_reqs_config],
            run_config={"ops": {"the_asset_reqs_config": {"config": {"bad": "foo"}}}},
        )


def test_materialize_resources():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("blah")})
    def the_asset(context):
        assert context.resources.foo == "blah"

    assert materialize([the_asset]).success


def test_materialize_resources_not_satisfied():
    @asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == "blah"

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'the_asset' was not provided",
    ):
        materialize([the_asset])

    assert materialize(
        with_resources([the_asset], {"foo": ResourceDefinition.hardcoded_resource("blah")})
    ).success


def test_materialize_conflicting_resources():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def first():
        pass

    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")})
    def second():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):
        materialize([first, second])


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

    result = materialize([the_asset, the_source])
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

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):
        materialize([the_asset, the_source])


def test_materialize_no_assets():
    assert materialize([]).success


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
        asset_keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        asset_keys_by_output_name={"result": AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )

    result = materialize([cool_thing_asset, a, b])
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
        asset_keys_by_input_name={},
        asset_keys_by_output_name={"o1": AssetKey("thing"), "o2": AssetKey("thing_2")},
        node_def=thing,
        asset_deps={AssetKey("thing"): set(), AssetKey("thing_2"): {AssetKey("thing")}},
    )

    @multi_asset(
        outs={
            "my_out_name": Out(metadata={"foo": "bar"}),
            "my_other_out_name": Out(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {AssetKey("my_other_out_name")},
            "my_other_out_name": {AssetKey("thing")},
        },
    )
    def multi_asset_with_internal_deps(thing):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    result = materialize([thing_asset, multi_asset_with_internal_deps])
    assert result.success
    assert result.output_for_node("multi_asset_with_internal_deps", "my_out_name") == 1
    assert result.output_for_node("multi_asset_with_internal_deps", "my_other_out_name") == 2
