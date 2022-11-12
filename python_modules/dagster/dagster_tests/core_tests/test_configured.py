import pytest

from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    ConfigMapping,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    IOManager,
    Output,
    asset,
    define_asset_job,
    graph,
    io_manager,
    materialize,
    multi_asset,
    op,
    repository,
    resource,
)
from dagster._legacy import ModeDefinition, execute_pipeline, pipeline, solid


def test_configured_solids_and_resources():
    # idiomatic usage
    @solid(config_schema={"greeting": str}, required_resource_keys={"animal", "plant"})
    def emit_greet_creature(context):
        greeting = context.solid_config["greeting"]
        return f"{greeting}, {context.resources.animal}, {context.resources.plant}"

    emit_greet_salutation = emit_greet_creature.configured(
        {"greeting": "salutation"}, "emit_greet_salutation"
    )

    emit_greet_howdy = emit_greet_creature.configured({"greeting": "howdy"}, "emit_greet_howdy")

    @resource(config_schema={"creature": str})
    def emit_creature(context):
        return context.resource_config["creature"]

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "animal": emit_creature.configured({"creature": "dog"}),
                    "plant": emit_creature.configured({"creature": "tree"}),
                }
            )
        ]
    )
    def mypipeline():
        return emit_greet_salutation(), emit_greet_howdy()

    result = execute_pipeline(mypipeline)

    assert result.success


get_asset_keys_from_materializations = lambda materializations: sorted(
    [materialization.asset_key for materialization in materializations]
)


def test_configured_asset():
    @asset(config_schema={"greeting": str}, key_prefix=["prefix"], group_name="my_group")
    def my_asset(context):
        return context.op_config["greeting"]

    configured_hello = my_asset.configured({"greeting": "hello"}, "configured_hello")
    assert configured_hello.group_names_by_key == {
        AssetKey(["prefix", "configured_hello"]): "my_group"
    }
    result = materialize([configured_hello])
    assert result.success
    assert result.output_for_node("configured_hello") == "hello"

    configured_hi = my_asset.configured({"greeting": "hi"}, "configured_hi")
    result = materialize([configured_hi])
    assert result.success
    assert result.output_for_node("configured_hi") == "hi"

    test_job = define_asset_job("test_job").resolve([configured_hello, configured_hi, my_asset], [])
    result = test_job.execute_in_process(
        run_config={"ops": {"prefix__my_asset": {"config": {"greeting": "hey"}}}}
    )
    assert result.success
    assert result.output_for_node("prefix__my_asset") == "hey"
    assert result.output_for_node("configured_hello") == "hello"
    assert result.output_for_node("configured_hi") == "hi"
    assert get_asset_keys_from_materializations(
        result.asset_materializations_for_node("prefix__my_asset")
    ) == [AssetKey(["prefix", "my_asset"])]
    assert get_asset_keys_from_materializations(
        result.asset_materializations_for_node("configured_hello")
    ) == [AssetKey(["prefix", "configured_hello"])]
    assert get_asset_keys_from_materializations(
        result.asset_materializations_for_node("configured_hi")
    ) == [AssetKey(["prefix", "configured_hi"])]


def test_configured_asset_with_io_manager_def():
    events = []

    class MyIOManager(IOManager):
        def handle_output(self, context, _obj):
            events.append(f"entered for {context.step_key}")

        def load_input(self, _context):
            pass

    @io_manager
    def the_io_manager():
        return MyIOManager()

    @asset(io_manager_def=the_io_manager, config_schema={"foo": str})
    def my_asset(context):
        return context.op_config["foo"]

    hello = my_asset.configured({"foo": "hello"}, "hello")
    result = materialize([hello])
    assert result.success
    assert result.output_for_node("hello") == "hello"

    hi = my_asset.configured({"foo": "hi"}, "hi")
    result = materialize([hi])
    assert result.success
    assert result.output_for_node("hi") == "hi"


def test_configured_multi_asset():
    @multi_asset(
        config_schema={"greeting": str, "farewell": str},
        outs={"foo": AssetOut(key=AssetKey(["prefix", "foo"])), "bar": AssetOut(key="bar")},
        group_name="my_group",
    )
    def my_multi_asset(context):
        yield Output(context.op_config["greeting"], "foo")
        yield Output(context.op_config["farewell"], "bar")

    configured_multi_asset = my_multi_asset.configured(
        {"greeting": "hello", "farewell": "bye"}, name="configured_multi_asset"
    )
    assert configured_multi_asset.group_names_by_key == {
        AssetKey(["prefix", "foo"]): "my_group",
        AssetKey("bar"): "my_group",
    }
    assert configured_multi_asset.keys == {AssetKey(["prefix", "foo"]), AssetKey("bar")}

    result = materialize([configured_multi_asset])
    assert result.success
    assert result.output_for_node("configured_multi_asset", "foo") == "hello"
    assert result.output_for_node("configured_multi_asset", "bar") == "bye"

    with pytest.raises(DagsterInvalidDefinitionError, match="Duplicate asset key"):

        @repository
        def invalid_repo():
            return [configured_multi_asset, my_multi_asset]

    @repository
    def my_repo():
        return [
            configured_multi_asset.with_prefix_or_group(
                output_asset_key_replacements={
                    AssetKey(["prefix", "foo"]): AssetKey("configured_foo"),
                    AssetKey("bar"): AssetKey("configured_bar"),
                }
            ),
            my_multi_asset,
            define_asset_job("combined_job"),
        ]

    result = my_repo.get_job("combined_job").execute_in_process(
        {"ops": {"my_multi_asset": {"config": {"farewell": "goodbye", "greeting": "hi"}}}}
    )
    assert result.success

    assert get_asset_keys_from_materializations(
        result.asset_materializations_for_node("my_multi_asset")
    ) == [AssetKey("bar"), AssetKey(["prefix", "foo"])]
    assert result.output_for_node("my_multi_asset", "foo") == "hi"
    assert result.output_for_node("my_multi_asset", "bar") == "goodbye"

    assert get_asset_keys_from_materializations(
        result.asset_materializations_for_node("configured_multi_asset")
    ) == [AssetKey("configured_bar"), AssetKey(["configured_foo"])]


def test_configured_graph_backed_asset():
    @op(config_schema={"foo": str})
    def requires_foo(context):
        return context.op_config["foo"]

    def _config_fn(outer):
        return {"requires_foo": {"config": {"foo": outer}}}

    @graph(config=ConfigMapping(config_fn=_config_fn, config_schema=str))
    def my_asset_graph():
        return requires_foo()

    with pytest.raises(DagsterInvalidInvocationError, match=".configured"):
        AssetsDefinition.from_graph(my_asset_graph).configured({"foo": "bar"}, name="new_asset")

    configured_asset = AssetsDefinition.from_graph(
        my_asset_graph.configured("bar", "configured_graph")
    )
    result = materialize([configured_asset])
    assert result.success
    assert result.output_for_node("configured_graph") == "bar"
