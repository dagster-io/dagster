from collections import defaultdict
from typing import Callable

import pytest
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager
from dagster.components.lib.executable_component.executable_component import (
    ExecutableComponent,
    make_materialize_result,
)
from dagster.components.lib.executable_component.execute import (
    components_to_defs,
    execute_asset_in_component,
    execute_assets_in_component,
    execute_assets_in_defs,
)
from dagster.components.lib.executable_component.load_input import load_input


def test_single_asset():
    assert ExecutableComponent


def test_basic_single_asset_return_none() -> None:
    def _execute_fn(context):
        return None

    component = ExecutableComponent(name="foo", assets=[AssetSpec("key")], execute_fn=_execute_fn)

    with pytest.raises(Exception, match="execute_fn must return a result"):
        execute_asset_in_component(component, "key")


def test_basic_single_asset_empty_result() -> None:
    def _execute_fn(context) -> MaterializeResult:
        return make_materialize_result()

    component = ExecutableComponent(name="foo", assets=[AssetSpec("key")], execute_fn=_execute_fn)

    evaluation = execute_asset_in_component(component, "key")
    assert evaluation.value is None


def test_basic_single_asset_with_value() -> None:
    def foo(context) -> MaterializeResult:
        return make_materialize_result(value="return_value")

    component = ExecutableComponent(assets=[AssetSpec("key")], execute_fn=foo)

    evaluation = execute_asset_in_component(component, "key")
    assert evaluation.value == "return_value"

    assert execute_assets_in_component(component, ["key"])[AssetKey("key")].value == "return_value"


def test_multiple_assets() -> None:
    def multiple_asset_execute(context):
        yield make_materialize_result(value="return_value_1", asset_key="key1")
        yield make_materialize_result(value="return_value_2", asset_key="key2")

    component = ExecutableComponent(
        name="foo",
        assets=[AssetSpec("key1"), AssetSpec("key2")],
        execute_fn=multiple_asset_execute,
    )

    evaluation = execute_assets_in_component(component, ["key1", "key2"])
    assert evaluation[AssetKey("key1")].value == "return_value_1"
    assert evaluation[AssetKey("key2")].value == "return_value_2"


def test_assets_with_resources() -> None:
    def _execute_fn(context, a_resource: ResourceParam[str]) -> MaterializeResult:
        return make_materialize_result(value=a_resource)

    component = ExecutableComponent(name="foo", assets=[AssetSpec("key")], execute_fn=_execute_fn)

    evaluation = execute_asset_in_component(component, "key", resources={"a_resource": "foo"})
    assert evaluation.value == "foo"


def test_deps() -> None:
    def _upstream_execute(context) -> MaterializeResult:
        return make_materialize_result()

    def _downstream_execute(
        context: AssetExecutionContext,
    ) -> MaterializeResult:
        return make_materialize_result()

    upstream_component = ExecutableComponent(
        name="upstream",
        assets=[AssetSpec("upstream_key")],
        execute_fn=_upstream_execute,
    )
    downstream_component = ExecutableComponent(
        name="downstream",
        assets=[AssetSpec("downstream_key", deps=["upstream_key"])],
        execute_fn=_downstream_execute,
    )
    defs = components_to_defs([upstream_component, downstream_component])
    evaluations = execute_assets_in_defs(defs, ["upstream_key", "downstream_key"])
    assert set(evaluations.keys()) == {AssetKey("upstream_key"), AssetKey("downstream_key")}


def test_parameter_passing_using_user_space_io_manager() -> None:
    class CountingInMemoryIOManager(IOManager):
        def __init__(self):
            self.values: dict[tuple[object, ...], object] = {}
            self.input_call_counts: defaultdict[str, int] = defaultdict(int)
            self.output_call_counts: defaultdict[str, int] = defaultdict(int)

        def handle_output(self, context: OutputContext, obj: object):
            keys = tuple(context.get_identifier())
            self.values[keys] = obj
            self.output_call_counts[context.asset_key.to_user_string()] += 1

        def load_input(self, context: InputContext) -> object:
            keys = tuple(context.get_identifier())
            self.input_call_counts[context.asset_key.to_user_string()] += 1
            return self.values[keys]

    def _upstream_execute(context) -> MaterializeResult:
        return make_materialize_result(value=1)

    def _downstream_execute(
        context: AssetExecutionContext,
    ) -> MaterializeResult:
        with load_input(context, "upstream_key", int) as upstream_key_value:
            return make_materialize_result(value=upstream_key_value + 1)

    upstream_component = ExecutableComponent(
        name="upstream",
        assets=[AssetSpec("upstream_key")],
        execute_fn=_upstream_execute,
    )

    downstream_component = ExecutableComponent(
        name="downstream",
        assets=[AssetSpec("downstream_key", deps=["upstream_key"])],
        execute_fn=_downstream_execute,
    )

    io_manager = CountingInMemoryIOManager()
    defs = components_to_defs([upstream_component, downstream_component]).with_resources(
        {"io_manager": io_manager}
    )
    evaluations = execute_assets_in_defs(defs, ["upstream_key", "downstream_key"])
    assert io_manager.input_call_counts["upstream_key"] == 1
    assert io_manager.output_call_counts["upstream_key"] == 1
    assert evaluations[AssetKey("upstream_key")].value == 1
    assert evaluations[AssetKey("downstream_key")].value == 2


def deps_from_execute(execute_fn: Callable) -> list[AssetDep]: ...
