import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Iterator, Type

import dagster._check as check
from dagster._core.definitions.events import Failure, RetryRequested
from dagster._core.errors import (
    DagsterError,
    DagsterExecutionInterruptedError,
    DagsterUserCodeExecutionError,
    raise_execution_interrupts,
)

if TYPE_CHECKING:
    from dagster._core.definitions.resource_definition import Resources
    from dagster._core.execution.context.system import StepExecutionContext


def build_resources_for_manager(
    io_manager_key: str, step_context: "StepExecutionContext"
) -> "Resources":
    required_resource_keys = step_context.mode_def.resource_defs[
        io_manager_key
    ].required_resource_keys
    return step_context.scoped_resources_builder.build(required_resource_keys)


@contextmanager
def solid_execution_error_boundary(
    error_cls: Type[DagsterUserCodeExecutionError],
    msg_fn: Callable[[], str],
    step_context: "StepExecutionContext",
    **kwargs: Any,
) -> Iterator[None]:
    """
    A specialization of user_code_error_boundary for the steps involved in executing a solid.
    This variant supports the control flow exceptions RetryRequested and Failure as well
    as respecting the RetryPolicy if present.
    """
    from dagster._core.execution.context.system import StepExecutionContext

    check.callable_param(msg_fn, "msg_fn")
    check.class_param(error_cls, "error_cls", superclass=DagsterUserCodeExecutionError)
    check.inst_param(step_context, "step_context", StepExecutionContext)

    with raise_execution_interrupts():

        step_context.log.begin_python_log_capture()
        retry_policy = step_context.solid_retry_policy

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

            if retry_policy:
                # if Failure with allow_retries set to false, disregard retry policy and raise
                if isinstance(e, Failure) and not e.allow_retries:
                    raise e

                raise RetryRequested(
                    max_retries=retry_policy.max_retries,
                    seconds_to_wait=retry_policy.calculate_delay(
                        step_context.previous_attempt_count + 1
                    ),
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

        except (DagsterExecutionInterruptedError, KeyboardInterrupt) as ie:
            # respect retry policy when interrupts occur
            if retry_policy:
                raise RetryRequested(
                    max_retries=retry_policy.max_retries,
                    seconds_to_wait=retry_policy.calculate_delay(
                        step_context.previous_attempt_count + 1
                    ),
                ) from ie
            else:
                raise ie

        finally:
            step_context.log.end_python_log_capture()
