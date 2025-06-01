from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional

import pytest
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import MaterializeResult
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component import ExecutableComponent, make_materialize_result


def test_single_asset():
    assert ExecutableComponent


class MaterializationEvaluation:
    def __init__(self, event: AssetMaterialization, value: Any):
        self.event = event
        self.value = value


def execute_asset_in_component(
    component: ExecutableComponent,
    asset_key: CoercibleToAssetKey,
    resources: Optional[dict[str, Any]] = None,
) -> MaterializationEvaluation:
    asset_key = AssetKey.from_coercible(asset_key)
    return execute_assets_in_component(component, [asset_key], resources)[asset_key]


def execute_assets_in_component(
    component: ExecutableComponent,
    asset_keys: list[CoercibleToAssetKey],
    resources: Optional[dict[str, Any]] = None,
) -> dict[AssetKey, MaterializationEvaluation]:
    return execute_assets_in_defs(
        component.build_defs(ComponentLoadContext.for_test()), asset_keys, resources
    )


def execute_assets_in_defs(
    defs: Definitions,
    asset_keys: list[CoercibleToAssetKey],
    resources: Optional[dict[str, Any]] = None,
) -> dict[AssetKey, MaterializationEvaluation]:
    full_asset_keys: list[AssetKey] = [AssetKey.from_coercible(key) for key in asset_keys]
    if resources:
        defs = defs.with_resources(resources)
    job_def = defs.get_implicit_job_def_for_assets(full_asset_keys)
    assert job_def

    result = job_def.execute_in_process()
    assert result.success

    evaluations = {}
    for asset_key in full_asset_keys:
        node_output_handle = job_def.asset_layer.node_output_handle_for_asset(asset_key)
        node_name = node_output_handle.node_handle.name

        materializations = result.asset_materializations_for_node(node_name)
        for materialization in materializations:
            evaluations[asset_key] = MaterializationEvaluation(
                event=materialization,
                value=result.output_for_node(
                    node_name, output_name=asset_key.to_python_identifier()
                ),
            )

    return evaluations


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


def components_to_defs(components: list[ExecutableComponent]) -> Definitions:
    return Definitions.merge(
        *[component.build_defs(ComponentLoadContext.for_test()) for component in components]
    )


def resource_dict(context: AssetExecutionContext) -> dict[str, Any]:
    return context.op_execution_context.resources.original_resource_dict


# def load_input_direct(context: AssetExecutionContext, input_name: str) -> Any:
#     step_context = context.get_step_execution_context()
#     step_input = step_context.step.step_input_named(input_name)
#     assert isinstance(step_input.source, FromStepOutput)
#     input_def = step_context.op_def.input_def_named(input_name)
#     io_manager_key = step_input.source.resolve_io_manager_key(step_context)
#     input_context = step_input.source.get_load_context(step_context, input_def, io_manager_key)
#     io_manager = resource_dict(context).get(io_manager_key)
#     assert isinstance(io_manager, InputManager)
#     return io_manager.load_input(input_context)


@contextmanager
def load_input_using_load_input_value(
    context: AssetExecutionContext, input_name: str
) -> Iterator[Any]:
    step_context = context.get_step_execution_context()
    step_input = step_context.step.step_input_named(input_name)
    input_def = step_context.op_def.input_def_named(input_name)
    iterator = step_input.source.load_input_object(step_context, input_def)
    for item in iterator:
        if isinstance(item, DagsterEvent):
            context.op_execution_context._events.append(item)  # noqa: SLF001
        else:
            yield item


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
        with load_input_using_load_input_value(context, "upstream_key") as upstream_key_value:
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


# defaultdict(<class 'int'>, {('38e55428-6de1-4638-b8d4-45381021d6d6', 'upstream', 'upstream_key'): 1, ('38e55428-6de1-4638-b8d4-45381021d6d6', 'downstream', 'downstream_key'): 1})
