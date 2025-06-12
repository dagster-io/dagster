from collections.abc import Generator, Mapping, Sequence
from typing import Callable, Optional, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetExecutionType, AssetSpec
from dagster._core.definitions.computation import Computation, Effect
from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
    DecoratorAssetsDefinitionBuilder,
    DecoratorAssetsDefinitionBuilderArgs,
    create_check_specs_by_output_name,
)
from dagster._core.definitions.result import AssetCheckResult, AssetResult

ComputationResult: TypeAlias = Generator[Union[AssetResult, AssetCheckResult], None, None]


@check.checked
def computation(
    *,
    specs: Sequence[Union[AssetSpec, AssetCheckSpec]],
    asset_execution_type: AssetExecutionType = AssetExecutionType.MATERIALIZATION,
    # compute node
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    pool: Optional[str] = None,
) -> Callable[[Callable[..., ComputationResult]], Computation]:
    asset_specs = [spec for spec in specs if isinstance(spec, AssetSpec)]
    asset_check_specs = [spec for spec in specs if isinstance(spec, AssetCheckSpec)]
    args = DecoratorAssetsDefinitionBuilderArgs(
        decorator_name="@computation",
        name=name,
        op_description=description,
        op_tags=tags,
        pool=pool,
        specs=asset_specs,
        check_specs_by_output_name=create_check_specs_by_output_name(asset_check_specs),
        can_subset=any(spec.skippable for spec in asset_specs),
        execution_type=asset_execution_type,
        allow_arbitrary_check_specs=True,
        # unset params
        asset_out_map={},
        asset_deps={},
        asset_in_map={},
        upstream_asset_deps=None,
        group_name=None,
        partitions_def=None,
        retry_policy=None,
        code_version=None,
        config_schema=None,
        compute_kind=None,
        required_resource_keys=set(),
        op_def_resource_defs={},
        assets_def_resource_defs={},
        backfill_policy=None,
        hooks=None,
    )

    def inner(fn: Callable[..., ComputationResult]) -> Computation:
        builder = DecoratorAssetsDefinitionBuilder.for_multi_asset(fn=fn, args=args)

        # TODO: move this logic into the builder
        node_def = builder.create_op_definition()

        output_names_by_key = {
            **{v: k for k, v in builder.asset_keys_by_output_name.items()},
            **{v.key: k for k, v in builder.check_specs_by_output_name.items()},
        }

        output_mappings = {}
        for spec in specs:
            output_name = output_names_by_key[spec.key]
            if isinstance(spec, AssetSpec):
                output_mappings[output_name] = (
                    Effect.observe(spec)
                    if asset_execution_type == AssetExecutionType.OBSERVATION
                    else Effect.materialize(spec)
                )
            else:
                output_mappings[output_name] = Effect.check(spec)

        return Computation(
            node_def=node_def,
            input_mappings=builder.asset_keys_by_input_name,
            output_mappings=output_mappings,
            inactive_outputs=set(),
        )

    return inner
