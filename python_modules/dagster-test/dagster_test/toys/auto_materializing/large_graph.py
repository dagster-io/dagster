import itertools
from typing import List, NamedTuple, Optional, Sequence

from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    AssetsDefinition,
    AutoMaterializePolicy,
    AutomationCondition,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MaterializeResult,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    repository,
)
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils.warnings import disable_dagster_warnings


class AssetLayerConfig(NamedTuple):
    n_assets: int
    n_upstreams_per_asset: int = 0
    partitions_def: Optional[PartitionsDefinition] = None
    n_checks_per_asset: int = 0


def build_assets(
    id: str,
    layer_configs: Sequence[AssetLayerConfig],
    automation_condition: Optional[AutomationCondition] = AutomationCondition.eager(),
) -> list[AssetsDefinition]:
    layers = []

    with disable_dagster_warnings():
        for layer_config in layer_configs:
            parent_index = 0
            layer = []
            for i in range(layer_config.n_assets):
                if layer_config.n_upstreams_per_asset > 0:
                    # each asset connects to n_upstreams_per_asset assets from the above layer, chosen
                    # in a round-robin manner
                    non_argument_deps = {
                        layers[-1][(parent_index + j) % len(layers[-1])].key
                        for j in range(layer_config.n_upstreams_per_asset)
                    }
                    parent_index += layer_config.n_upstreams_per_asset
                else:
                    non_argument_deps = set()

                name = f"{id}_{len(layers)}_{i}"

                @asset(
                    partitions_def=layer_config.partitions_def,
                    name=name,
                    automation_condition=automation_condition,
                    non_argument_deps=non_argument_deps,
                    check_specs=[
                        AssetCheckSpec(
                            name=f"check{k}",
                            asset=AssetKey(name),
                            automation_condition=automation_condition,
                        )
                        for k in range(layer_config.n_checks_per_asset)
                    ],
                )
                def _asset(context: AssetExecutionContext) -> MaterializeResult:
                    return MaterializeResult(
                        asset_key=context.asset_key,
                        check_results=[
                            AssetCheckResult(check_name=key.name, passed=True)
                            for key in context.selected_asset_check_keys
                        ],
                    )

                layer.append(_asset)
            layers.append(layer)

    return list(itertools.chain(*layers))


hourly = HourlyPartitionsDefinition(start_date="2022-01-01-00:00")
daily = DailyPartitionsDefinition(
    start_date="2022-01-01",
)
static = StaticPartitionsDefinition(partition_keys=[f"p{i}" for i in range(100)])


@repository
def auto_materialize_large_time_graph():
    return build_assets(
        id="hourly_to_daily",
        layer_configs=[
            AssetLayerConfig(n_assets=10, partitions_def=hourly),
            AssetLayerConfig(n_assets=50, n_upstreams_per_asset=5, partitions_def=hourly),
            AssetLayerConfig(n_assets=50, n_upstreams_per_asset=5, partitions_def=hourly),
            AssetLayerConfig(n_assets=100, n_upstreams_per_asset=4, partitions_def=daily),
            AssetLayerConfig(n_assets=100, n_upstreams_per_asset=4, partitions_def=daily),
        ],
        automation_condition=AutoMaterializePolicy.eager().to_automation_condition(),
    )


@repository
def auto_materialize_large_static_graph():
    return build_assets(
        id="static_and_unpartitioned",
        layer_configs=[
            AssetLayerConfig(n_assets=10, partitions_def=None),
            AssetLayerConfig(n_assets=50, n_upstreams_per_asset=5, partitions_def=static),
            AssetLayerConfig(n_assets=50, n_upstreams_per_asset=5, partitions_def=static),
            AssetLayerConfig(n_assets=100, n_upstreams_per_asset=4, partitions_def=static),
            AssetLayerConfig(n_assets=100, n_upstreams_per_asset=4, partitions_def=None),
        ],
        automation_condition=AutoMaterializePolicy.eager().to_automation_condition(),
    )
