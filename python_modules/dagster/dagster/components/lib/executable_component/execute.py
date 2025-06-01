from typing import Any, Optional

from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.executable_component import ExecutableComponent


def components_to_defs(components: list[ExecutableComponent]) -> Definitions:
    return Definitions.merge(
        *[component.build_defs(ComponentLoadContext.for_test()) for component in components]
    )


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
