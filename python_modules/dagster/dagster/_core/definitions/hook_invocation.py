from typing import TYPE_CHECKING, Optional, Sequence

import dagster._check as check

from ..execution.context.hook import BoundHookContext, UnboundHookContext
from .resource_requirement import ensure_requirements_satisfied

if TYPE_CHECKING:
    from ..events import DagsterEvent
    from .hook_definition import HookDefinition


def hook_invocation_result(
    hook_def: "HookDefinition",
    hook_context: Optional[UnboundHookContext],
    event_list: Optional[Sequence["DagsterEvent"]] = None,
):
    if not hook_context:
        hook_context = UnboundHookContext(
            resources={}, op=None, run_id=None, job_name=None, op_exception=None
        )

    # Validate that all required resources are provided in the context
    # pylint: disable=protected-access
    ensure_requirements_satisfied(
        hook_context._resource_defs, list(hook_def.get_resource_requirements())
    )

    bound_context = BoundHookContext(
        hook_def=hook_def,
        resources=hook_context.resources,
        log_manager=hook_context.log,
        op=hook_context._op,
        run_id=hook_context._run_id,
        job_name=hook_context._job_name,
        op_exception=hook_context._op_exception,
    )

    decorated_fn = check.not_none(hook_def.decorated_fn)

    return (
        decorated_fn(bound_context, event_list)
        if event_list is not None
        else decorated_fn(bound_context)
    )
