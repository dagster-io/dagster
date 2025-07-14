import dagster as dg
from dagster import AssetsDefinition


def materialize_expect_metadata(assets_def: AssetsDefinition):
    @dg.asset(ins={key.path[-1]: dg.AssetIn(key) for key in assets_def.keys})
    def downstream_asset(**kwargs): ...

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            if context.asset_key != downstream_asset.key:
                assert context.definition_metadata["fruit"] == "apple"

        def load_input(self, context):
            assert context.upstream_output.definition_metadata["fruit"] == "apple"  # pyright: ignore[reportOptionalMemberAccess]

    assert dg.materialize(
        assets=[assets_def, downstream_asset],
        resources={"io_manager": MyIOManager()},
    ).success


def test_asset_with_metadata():
    @dg.asset(metadata={"fruit": "apple"})
    def basic_asset_with_metadata(): ...

    materialize_expect_metadata(basic_asset_with_metadata)


def test_multi_asset_with_metadata():
    @dg.multi_asset(outs={"asset1": dg.AssetOut(metadata={"fruit": "apple"})})
    def multi_asset_with_metadata(): ...

    materialize_expect_metadata(multi_asset_with_metadata)


def test_graph_asset_outer_metadata():
    @dg.op
    def op_without_output_metadata(): ...

    @dg.graph_multi_asset(outs={"asset1": dg.AssetOut(metadata={"fruit": "apple"})})
    def graph_with_outer_metadata():
        return op_without_output_metadata()

    materialize_expect_metadata(graph_with_outer_metadata)


def test_assets_definition_from_graph_metadata():
    @dg.op
    def op_without_output_metadata(): ...

    @dg.graph(out={"asset1": dg.GraphOut()})
    def graph_without_metadata():
        return op_without_output_metadata()

    materialize_expect_metadata(
        AssetsDefinition.from_graph(
            graph_without_metadata, metadata_by_output_name={"asset1": {"fruit": "apple"}}
        )
    )
