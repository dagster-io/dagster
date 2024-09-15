from typing import Any

from dagster import (
    AssetKey,
    AssetSpec,
    IOManager,
    OutputContext,
    StaticPartitionsDefinition,
    build_output_context,
    materialize,
)
from dagster._core.execution.context.input import InputContext


def test_build_output_context_asset_key():
    assert build_output_context(asset_key="apple").asset_key == AssetKey("apple")
    assert build_output_context(asset_key=["apple", "banana"]).asset_key == AssetKey(
        ["apple", "banana"]
    )
    assert build_output_context(asset_key=AssetKey("apple")).asset_key == AssetKey("apple")


def test_build_output_context_asset_spec():
    asset_spec = AssetSpec(
        key="key",
        group_name="group",
        code_version="code_version",
        partitions_def=StaticPartitionsDefinition(["part1"]),
    )

    class TestIOManager(IOManager):
        def handle_output(self, context: OutputContext, obj: object):
            assert context.asset_spec == asset_spec

        def load_input(self, context: InputContext) -> Any:
            pass

    materialize([asset_spec], resources={"io_manager": TestIOManager()})
