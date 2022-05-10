from typing import TYPE_CHECKING, List, NamedTuple, Optional, cast

import dagster._check as check

from ..errors import DagsterInvariantViolationError
from ..execution.context.hook import BoundHookContext, UnboundHookContext

if TYPE_CHECKING:
    from ..events import DagsterEvent
    from .hook_definition import HookDefinition


def hook_invocation_result(
    hook_def: "HookDefinition",
    hook_context: Optional[UnboundHookContext],
    event_list: Optional[List["DagsterEvent"]] = None,
):
    if not hook_context:
        hook_context = UnboundHookContext(
            resources={}, mode_def=None, op=None, run_id=None, job_name=None, op_exception=None
        )

    # Validate that all required resources are provided in the context
    for key in hook_def.required_resource_keys:
        resources = cast(NamedTuple, hook_context.resources)
        if key not in resources._asdict():
            raise DagsterInvariantViolationError(
                f"The hook '{hook_def.name}' requires resource '{key}', which was not provided by "
                "the context."
            )

    # pylint: disable=protected-access

    bound_context = BoundHookContext(
        hook_def=hook_def,
        resources=hook_context.resources,
        mode_def=hook_context.mode_def,
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
