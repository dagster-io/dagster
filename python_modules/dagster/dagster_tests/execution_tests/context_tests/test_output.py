from typing import Any

import dagster as dg
from dagster import OutputContext
from dagster._core.execution.context.input import InputContext


def test_build_output_context_asset_key():
    assert dg.build_output_context(asset_key="apple").asset_key == dg.AssetKey("apple")
    assert dg.build_output_context(asset_key=["apple", "banana"]).asset_key == dg.AssetKey(
        ["apple", "banana"]
    )
    assert dg.build_output_context(asset_key=dg.AssetKey("apple")).asset_key == dg.AssetKey("apple")


def test_build_output_context_asset_spec():
    asset_spec = dg.AssetSpec(
        key="key",
        group_name="group",
        code_version="code_version",
        partitions_def=dg.StaticPartitionsDefinition(["part1"]),
    )

    class TestIOManager(dg.IOManager):
        def handle_output(self, context: OutputContext, obj: object):
            assert context.asset_spec == asset_spec

        def load_input(self, context: InputContext) -> Any:
            pass

    dg.materialize([asset_spec], resources={"io_manager": TestIOManager()})


def test_build_output_context_with_output_metadata():
    expected_metadata = {"foo": "bar"}
    output_context = dg.build_output_context(output_metadata=expected_metadata)

    class TestIOManager(dg.IOManager):
        def handle_output(self, context: OutputContext, obj: object):
            assert context.output_metadata == expected_metadata

        def load_input(self, context: InputContext) -> Any:
            pass

    io_manager = TestIOManager()
    io_manager.handle_output(output_context, "test")
