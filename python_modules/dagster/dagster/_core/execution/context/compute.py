from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from inspect import _empty as EmptyAnnotation
from typing import Optional, Union

from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.execution.context.system import StepExecutionContext

ExecutionContextTypes = Union[OpExecutionContext, AssetExecutionContext, AssetCheckExecutionContext]


@contextmanager
def enter_execution_context(
    step_context: StepExecutionContext,
) -> Iterator[ExecutionContextTypes]:
    """Get the correct context based on the type of step (op or asset) and the user provided context
    type annotation. Follows these rules.

    step type     annotation                   result
    asset         AssetExecutionContext        AssetExecutionContext
    asset         AssetCheckExecutionContext   Error - not an asset check
    asset         OpExecutionContext           OpExecutionContext
    asset         None                         AssetExecutionContext
    op            AssetExecutionContext        Error - we cannot init an AssetExecutionContextext w/o an AssetsDefinition
    op            AssetCheckExecutionContext   Error - not an asset check
    op            OpExecutionContext           OpExecutionContext
    op            None                         OpExecutionContext
    asset_check   AssetCheckExecutionContext   AssetCheckExecutionContext
    asset_check   AssetExecutionContext        Error - not an asset
    asset_check   OpExecutionContext           OpExecutionContext
    asset_check   None                         AssetCheckExecutionContext

    For ops in graph-backed assets
    step type     annotation                   result
    op            AssetExecutionContext        AssetExecutionContext
    op            AssetCheckExecutionContext   Error - not an asset check
    op            OpExecutionContext           OpExecutionContext
    op            None                         OpExecutionContext

    """
    is_sda_step = step_context.is_sda_step
    is_op_in_graph_asset = step_context.is_in_graph_asset
    asset_check_only_step = (
        step_context.is_asset_check_step and not is_sda_step and not is_op_in_graph_asset
    )
    context_annotation = EmptyAnnotation
    compute_fn = step_context.op_def._compute_fn  # noqa: SLF001
    compute_fn = (
        compute_fn
        if isinstance(compute_fn, DecoratedOpFunction)
        else DecoratedOpFunction(compute_fn)
    )
    if compute_fn.has_context_arg():
        context_param = compute_fn.get_context_arg()
        context_annotation = context_param.annotation

    if context_annotation is AssetCheckExecutionContext and not asset_check_only_step:
        if is_sda_step:
            raise DagsterInvalidDefinitionError(
                "Cannot annotate @asset `context` parameter with type AssetCheckExecutionContext. "
                "`context` must be annotated with AssetExecutionContext, OpExecutionContext, or left blank."
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Cannot annotate @op `context` parameter with type AssetCheckExecutionContext. "
                "`context` must be annotated with OpExecutionContext, AssetExecutionContext (if part of "
                "a graph-backed-asset) or left blank."
            )

    if context_annotation is AssetExecutionContext:
        if asset_check_only_step:
            raise DagsterInvalidDefinitionError(
                "Cannot annotate @asset_check `context` parameter with type AssetExecutionContext. "
                "`context` must be annotated with AssetCheckExecutionContext, OpExecutionContext, or left blank."
            )

        # It would be nice to do this check at definition time, rather than at run time, but we don't
        # know if the op is part of an op job or a graph-backed asset until we have the step execution context
        if not is_sda_step and not is_op_in_graph_asset:
            # AssetExecutionContext requires an AssetsDefinition during init, so an op in an op job
            # cannot be annotated with AssetExecutionContext
            raise DagsterInvalidDefinitionError(
                "Cannot annotate @op `context` parameter with type AssetExecutionContext unless the"
                " op is part of a graph-backed asset. `context` must be annotated with"
                " OpExecutionContext, or left blank."
            )

    # default to AssetCheckExecutionContext in @asset_checks
    if asset_check_only_step and context_annotation is not OpExecutionContext:
        asset_ctx = AssetCheckExecutionContext(
            op_execution_context=OpExecutionContext(step_context)
        )
    else:
        asset_ctx = AssetExecutionContext(op_execution_context=OpExecutionContext(step_context))

    asset_token = current_execution_context.set(asset_ctx)

    try:
        if context_annotation is EmptyAnnotation:
            # if no type hint has been given, default to:
            # * AssetExecutionContext for sda steps not in graph-backed assets, and asset_checks
            # * OpExecutionContext for non sda steps
            # * OpExecutionContext for ops in graph-backed assets
            if asset_check_only_step:
                yield asset_ctx
            elif is_op_in_graph_asset or not is_sda_step:
                yield asset_ctx.op_execution_context
            else:
                yield asset_ctx
        elif (
            context_annotation is AssetExecutionContext
            or context_annotation is AssetCheckExecutionContext
        ):
            yield asset_ctx
        else:
            yield asset_ctx.op_execution_context
    finally:
        current_execution_context.reset(asset_token)


current_execution_context: ContextVar[
    Optional[Union[AssetExecutionContext, AssetCheckExecutionContext]]
] = ContextVar("current_execution_context", default=None)
