from dagster import (
    AssetIn,
    AssetOut,
    AssetsDefinition,
    GraphOut,
    asset,
    graph,
    graph_multi_asset,
    materialize,
    multi_asset,
    op,
)
from dagster._core.storage.io_manager import IOManager


def materialize_expect_metadata(assets_def: AssetsDefinition):
    @asset(ins={key.path[-1]: AssetIn(key) for key in assets_def.keys})
    def downstream_asset(**kwargs): ...

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            if context.asset_key != downstream_asset.key:
                assert context.definition_metadata["fruit"] == "apple"

        def load_input(self, context):
            assert context.upstream_output.definition_metadata["fruit"] == "apple"  # pyright: ignore[reportOptionalMemberAccess]

    assert materialize(
        assets=[assets_def, downstream_asset],
        resources={"io_manager": MyIOManager()},
    ).success


def test_asset_with_metadata():
    @asset(metadata={"fruit": "apple"})
    def basic_asset_with_metadata(): ...

    materialize_expect_metadata(basic_asset_with_metadata)


def test_multi_asset_with_metadata():
    @multi_asset(outs={"asset1": AssetOut(metadata={"fruit": "apple"})})
    def multi_asset_with_metadata(): ...

    materialize_expect_metadata(multi_asset_with_metadata)


def test_graph_asset_outer_metadata():
    @op
    def op_without_output_metadata(): ...

    @graph_multi_asset(outs={"asset1": AssetOut(metadata={"fruit": "apple"})})
    def graph_with_outer_metadata():
        return op_without_output_metadata()

    materialize_expect_metadata(graph_with_outer_metadata)


def test_assets_definition_from_graph_metadata():
    @op
    def op_without_output_metadata(): ...

    @graph(out={"asset1": GraphOut()})
    def graph_without_metadata():
        return op_without_output_metadata()

    materialize_expect_metadata(
        AssetsDefinition.from_graph(
            graph_without_metadata, metadata_by_output_name={"asset1": {"fruit": "apple"}}
        )
    )
