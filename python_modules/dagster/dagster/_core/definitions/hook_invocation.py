from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.execution.context.hook import BoundHookContext, UnboundHookContext

if TYPE_CHECKING:
    from dagster._core.definitions.hook_definition import HookDefinition
    from dagster._core.events import DagsterEvent


def hook_invocation_result(
    hook_def: "HookDefinition",
    hook_context: Optional[UnboundHookContext],
    event_list: Optional[Sequence["DagsterEvent"]] = None,
):
    if not hook_context:
        hook_context = UnboundHookContext(
            resources={}, op=None, run_id=None, job_name=None, op_exception=None, instance=None
        )

    # Validate that all required resources are provided in the context

    ensure_requirements_satisfied(
        hook_context._resource_defs,  # noqa: SLF001
        list(hook_def.get_resource_requirements(attached_to=None)),
    )

    bound_context = BoundHookContext(
        hook_def=hook_def,
        resources=hook_context.resources,
        log_manager=hook_context.log,
        op=hook_context._op,  # noqa: SLF001
        run_id=hook_context._run_id,  # noqa: SLF001
        job_name=hook_context._job_name,  # noqa: SLF001
        op_exception=hook_context._op_exception,  # noqa: SLF001
        instance=hook_context._instance,  # noqa: SLF001
    )

    decorated_fn = check.not_none(hook_def.decorated_fn)

    return (
        decorated_fn(bound_context, event_list)
        if event_list is not None
        else decorated_fn(bound_context)
    )
