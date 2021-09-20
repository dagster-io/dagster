from typing import TYPE_CHECKING, List, NamedTuple, Optional, cast

from ..errors import DagsterInvariantViolationError
from ..execution.context.hook import BoundHookContext, UnboundHookContext

if TYPE_CHECKING:
    from .hook import HookDefinition
    from ..events import DagsterEvent


def hook_invocation_result(
    hook_def: "HookDefinition",
    hook_context: Optional[UnboundHookContext],
    event_list: Optional[List["DagsterEvent"]] = None,
):
    if not hook_context:
        hook_context = UnboundHookContext(resources={}, mode_def=None, solid=None)

    # Validate that all required resources are provided in the context
    for key in hook_def.required_resource_keys:
        resources = cast(NamedTuple, hook_context.resources)
        if key not in resources._asdict():
            raise DagsterInvariantViolationError(
                f"The hook '{hook_def.name}' requires resource '{key}', which was not provided by "
                "the context."
            )

    bound_context = BoundHookContext(
        hook_def=hook_def,
        resources=hook_context.resources,
        mode_def=hook_context.mode_def,
        log_manager=hook_context.log,
        solid=hook_context._solid,  # pylint: disable=protected-access
    )

    return (
        hook_def.decorated_fn(bound_context, event_list)
        if event_list is not None
        else hook_def.decorated_fn(bound_context)
    )
