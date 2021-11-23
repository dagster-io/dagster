import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

from dagster import check
from dagster.core.definitions.events import Failure, RetryRequested
from dagster.core.errors import (
    DagsterError,
    DagsterUserCodeExecutionError,
    raise_execution_interrupts,
)

if TYPE_CHECKING:
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.definitions.resource_definition import Resources


def build_resources_for_manager(
    io_manager_key: str, step_context: "StepExecutionContext"
) -> "Resources":
    required_resource_keys = step_context.mode_def.resource_defs[
        io_manager_key
    ].required_resource_keys
    return step_context.scoped_resources_builder.build(required_resource_keys)


@contextmanager
def solid_execution_error_boundary(error_cls, msg_fn, step_context, **kwargs):
    """
    A specialization of user_code_error_boundary for the steps involved in executing a solid.
    This variant supports the control flow exceptions RetryRequested and Failure as well
    as respecting the RetryPolicy if present.
    """
    from dagster.core.execution.context.system import StepExecutionContext

    check.callable_param(msg_fn, "msg_fn")
    check.subclass_param(error_cls, "error_cls", DagsterUserCodeExecutionError)
    check.inst_param(step_context, "step_context", StepExecutionContext)

    with raise_execution_interrupts():

        step_context.log.begin_python_log_capture()
        try:
            yield
        except DagsterError as de:
            # The system has thrown an error that is part of the user-framework contract
            raise de
        except Exception as e:  # pylint: disable=W0703
            # An exception has been thrown by user code and computation should cease
            # with the error reported further up the stack

            # Directly thrown RetryRequested escalate before evaluating the retry policy.
            if isinstance(e, RetryRequested):
                raise e

            policy = step_context.solid_retry_policy
            if policy:
                # could check exc against a whitelist of exceptions
                raise RetryRequested(
                    max_retries=policy.max_retries,
                    # likely to move the declarative properties on to the request (or just the whole policy)
                    seconds_to_wait=policy.calculate_delay(step_context.previous_attempt_count + 1),
                ) from e

            # Failure exceptions get re-throw without wrapping
            if isinstance(e, Failure):
                raise e

            # Otherwise wrap the user exception with context
            raise error_cls(
                msg_fn(),
                user_exception=e,
                original_exc_info=sys.exc_info(),
                **kwargs,
            ) from e
        finally:
            step_context.log.end_python_log_capture()
