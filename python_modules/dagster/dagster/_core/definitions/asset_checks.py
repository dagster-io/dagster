from typing import (
    Any,
    Mapping,
    Optional,
    Sequence,
)

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.errors import DagsterAssetCheckFailedError
from dagster._core.types.dagster_type import Nothing


class AssetChecksDefinition(AssetsDefinition):
    """Defines a set of checks that are produced by the same op or op graph.

    AssetChecksDefinition should not be instantiated directly, but rather produced using the `@asset_check` decorator or `AssetChecksDefinition.create` method.
    """

    @staticmethod
    def create(
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        node_def: OpDefinition,
        check_specs_by_output_name: Mapping[str, AssetCheckSpec],
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ):
        """Create an AssetChecksDefinition."""
        return AssetChecksDefinition(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={},
            node_def=node_def,
            partitions_def=None,
            partition_mappings=None,
            asset_deps=None,
            selected_asset_keys=None,
            can_subset=False,
            resource_defs=resource_defs,
            group_names_by_key=None,
            metadata_by_key=None,
            tags_by_key=None,
            freshness_policies_by_key=None,
            auto_materialize_policies_by_key=None,
            backfill_policy=None,
            descriptions_by_key=None,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,
            is_subset=False,
            owners_by_key=None,
        )


# This is still needed in a few places where we need to handle normal AssetsDefinition and
# AssetChecksDefinition differently, but eventually those areas should be refactored and this should
# be removed.
def has_only_asset_checks(assets_def: AssetsDefinition) -> bool:
    return len(assets_def.keys) == 0 and len(assets_def.check_keys) > 0


@experimental
def build_asset_with_blocking_check(
    asset_def: "AssetsDefinition",
    checks: Sequence["AssetsDefinition"],
) -> "AssetsDefinition":
    from dagster import AssetIn, In, OpExecutionContext, Output, op
    from dagster._core.definitions.decorators.asset_decorator import graph_asset_no_defaults
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus

    check_specs = []
    for c in checks:
        check_specs.extend(c.check_specs)

    check_output_names = [c.get_python_identifier() for c in check_specs]

    check.invariant(len(asset_def.op.output_defs) == 1)
    asset_out_type = asset_def.op.output_defs[0].dagster_type

    @op(
        name=f"{asset_def.op.name}_asset_and_checks",
        ins={"asset_return_value": In(asset_out_type), "check_evaluations": In(Nothing)},
    )
    def fan_in_checks_and_asset_return_value(context: OpExecutionContext, asset_return_value: Any):
        # we pass the asset_return_value through and store it again so that downstream assets can load it.
        # This is a little silly- we only do this because this op has the asset key in its StepOutputProperties
        # so the output is written to the right path. We could probably get the asset_def.op to write to the
        # asset path (and make sure we don't override it here) to avoid the double write.
        yield Output(asset_return_value)

        for check_spec in check_specs:
            executions = context.instance.event_log_storage.get_asset_check_execution_history(
                check_key=check_spec.key, limit=1
            )
            check.invariant(
                len(executions) == 1, "Expected asset check {check_spec.name} to execute"
            )
            execution = executions[0]
            check.invariant(
                execution.run_id == context.run_id,
                "Expected asset check {check_spec.name} to execute in the current run",
            )
            if execution.status != AssetCheckExecutionRecordStatus.SUCCEEDED:
                raise DagsterAssetCheckFailedError()

    # kwargs are the inputs to the asset_def.op that we are wrapping
    def blocking_asset(**kwargs):
        asset_return_value = asset_def.op.with_replaced_properties(
            name=f"{asset_def.op.name}_graph_asset_op"
        )(**kwargs)
        check_evaluations = [check.node_def(asset_return_value) for check in checks]

        return {
            "result": fan_in_checks_and_asset_return_value(asset_return_value, check_evaluations),
            **{
                check_output_name: check_result
                for check_output_name, check_result in zip(check_output_names, check_evaluations)
            },
        }

    return graph_asset_no_defaults(
        compose_fn=blocking_asset,
        name=None,
        key_prefix=None,
        key=asset_def.key,
        group_name=asset_def.group_names_by_key.get(asset_def.key),
        partitions_def=asset_def.partitions_def,
        check_specs=check_specs,
        description=asset_def.descriptions_by_key.get(asset_def.key),
        ins={name: AssetIn(key) for name, key in asset_def.keys_by_input_name.items()},
        resource_defs=asset_def.resource_defs,
        metadata=asset_def.metadata_by_key.get(asset_def.key),
        freshness_policy=asset_def.freshness_policies_by_key.get(asset_def.key),
        auto_materialize_policy=asset_def.auto_materialize_policies_by_key.get(asset_def.key),
        backfill_policy=asset_def.backfill_policy,
        config=None,  # gets config from asset_def.op
    )
