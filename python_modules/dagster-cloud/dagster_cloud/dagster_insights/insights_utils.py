from dataclasses import replace

import dagster._check as check
from dagster import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DagsterInvariantViolationError,
    OpExecutionContext,
    Output,
)
from dagster._core.errors import DagsterInvalidPropertyError


def get_current_context_and_asset_key() -> tuple[
    OpExecutionContext | AssetExecutionContext, AssetKey | None
]:
    asset_key = None
    try:
        context = AssetExecutionContext.get()
        if len(context.assets_def.keys_by_output_name.keys()) == 1:
            asset_key = context.asset_key
    except (DagsterInvalidPropertyError, DagsterInvariantViolationError):
        context = OpExecutionContext.get()

    return check.not_none(context), asset_key


def get_asset_key_for_output(
    context: OpExecutionContext | AssetExecutionContext, output_name: str
) -> AssetKey | None:
    asset_key = context.job_def.asset_layer.get_asset_key_for_node_output(
        node_handle=context.op_handle, output_name=output_name
    )
    if asset_key is None:
        return None
    return asset_key


def extract_asset_info_from_event(
    context,
    dagster_event: Output
    | AssetMaterialization
    | AssetObservation
    | AssetCheckResult
    | AssetCheckEvaluation,
    record_observation_usage,
):
    if isinstance(dagster_event, AssetMaterialization):
        return dagster_event.asset_key, dagster_event.partition

    if (
        isinstance(dagster_event, (AssetCheckResult, AssetObservation, AssetCheckEvaluation))
        and record_observation_usage
    ):
        partition = dagster_event.partition if isinstance(dagster_event, AssetObservation) else None
        return dagster_event.asset_key, partition

    if isinstance(dagster_event, (AssetCheckResult, AssetObservation, AssetCheckEvaluation)):
        return None, None

    if isinstance(dagster_event, Output):
        asset_key = get_asset_key_for_output(context, dagster_event.output_name)
        partition_key = None
        if asset_key and context._step_execution_context.has_asset_partitions_for_output(  # noqa: SLF001
            dagster_event.output_name
        ):
            # We associate cost with the first partition key in the case that an output
            # maps to multiple partitions. This is a temporary solution, but partition key
            # is not used in Insights at the moment.
            # TODO: Find a long-term solution for this
            partition_key = next(
                iter(context.asset_partition_keys_for_output(dagster_event.output_name))
            )

        return asset_key, partition_key

    return None, None


def handle_raise_on_error(invocation_arg_name: str, arg_position: int = 1):
    # defer import since dagster_cloud shouldn't depend on dagster_dbt
    # but this should only be used in envs that have dagster_dbt
    from dagster_dbt import DbtCliInvocation

    def raise_decorator(wrapper_fn):
        def inner(*args, **kwargs):
            from_args = len(args) > arg_position
            dbt_cli_invocation = (
                args[arg_position] if from_args else kwargs.get(invocation_arg_name)
            )
            assert isinstance(dbt_cli_invocation, DbtCliInvocation)

            # If the user has set raise_on_error=True, we want to raise the error, but not before we're
            # able to emit the cost information.  This context manager provides a replacement invocation
            # that will not raise, but will handle errors after the context is returned
            raise_on_error = dbt_cli_invocation.raise_on_error

            if not raise_on_error:
                yield from wrapper_fn(*args, **kwargs)
                return

            stubbed_dbt_cli_invocation = replace(dbt_cli_invocation, raise_on_error=False)
            new_args = (
                [
                    *args[:arg_position],
                    stubbed_dbt_cli_invocation,
                    *args[arg_position + 1 :],
                ]
                if from_args
                else args
            )
            new_kwargs = (
                {
                    **kwargs,
                    invocation_arg_name: stubbed_dbt_cli_invocation,
                }
                if not from_args
                else kwargs
            )
            yield from wrapper_fn(*new_args, **new_kwargs)
            error = stubbed_dbt_cli_invocation.get_error()
            if error and raise_on_error:
                raise error

        return inner

    return raise_decorator
