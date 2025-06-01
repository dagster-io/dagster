from typing import Any, Optional

import pytest
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
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

    evaluations = {}
    for asset_key in full_asset_keys:
        node_output_handle = job_def.asset_layer.node_output_handle_for_asset(asset_key)
        node_name = node_output_handle.node_handle.name

        result = job_def.execute_in_process()
        assert result.success

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


@pytest.mark.skip(reason="TODO: fix this test")
def test_parameter_passing() -> None:
    def _upstream_execute(context) -> MaterializeResult:
        return make_materialize_result(value=1)

    def _downstream_execute(
        context: AssetExecutionContext,
    ) -> MaterializeResult:
        raise Exception("TODO: fix this test")
        # upstream_key_value = load_input(context, "upstream_key")
        # return make_materialize_result(value=upstream_key_value + 1)

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
    assert evaluations[AssetKey("upstream_key")].value == 1
    assert evaluations[AssetKey("downstream_key")].value == 2
