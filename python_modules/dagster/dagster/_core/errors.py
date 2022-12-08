"""Core Dagster error classes.

All errors thrown by the Dagster framework inherit from :py:class:`~dagster.DagsterError`. Users
should not subclass this base class for their own exceptions.

There is another exception base class, :py:class:`~dagster.DagsterUserCodeExecutionError`, which is
used by the framework in concert with the :py:func:`~dagster._core.errors.user_code_error_boundary`.

Dagster uses this construct to wrap user code into which it calls. User code can perform arbitrary
computations and may itself throw exceptions. The error boundary catches these user code-generated
exceptions, and then reraises them wrapped in a subclass of
:py:class:`~dagster.DagsterUserCodeExecutionError`.

The wrapped exceptions include additional context for the original exceptions, injected by the
Dagster runtime.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, Iterator, Optional, Type

import dagster._check as check
from dagster._utils.interrupts import raise_interrupts_as

if TYPE_CHECKING:
    from dagster._core.log_manager import DagsterLogManager


class DagsterExecutionInterruptedError(BaseException):
    """
    Pipeline execution was interrupted during the execution process.

    Just like KeyboardInterrupt this inherits from BaseException
    as to not be accidentally caught by code that catches Exception
    and thus prevent the interpreter from exiting.
    """


class DagsterError(Exception):
    """Base class for all errors thrown by the Dagster framework.

    Users should not subclass this base class for their own exceptions."""

    @property
    def is_user_code_error(self):
        """Returns true if this error is attributable to user code."""
        return False


class DagsterInvalidDefinitionError(DagsterError):
    """Indicates that the rules for a definition have been violated by the user."""


class DagsterInvalidObservationError(DagsterError):
    """Indicates that an invalid value was returned from a source asset observation function."""


class DagsterInvalidSubsetError(DagsterError):
    """Indicates that a subset of a pipeline is invalid because either:
    - One or more ops in the specified subset do not exist on the job.'
    - The subset produces an invalid job.
    """


CONFIG_ERROR_VERBIAGE = """
This value can be a:
    - Field
    - Python primitive types that resolve to dagster config types
        - int, float, bool, str, list.
    - A dagster config type: Int, Float, Bool, Array, Optional, Selector, Shape, Permissive, Map
    - A bare python dictionary, which is wrapped in Field(Shape(...)). Any values
      in the dictionary get resolved by the same rules, recursively.
    - A python list with a single entry that can resolve to a type, e.g. [int]
"""


class DagsterInvalidConfigDefinitionError(DagsterError):
    """Indicates that you have attempted to construct a config with an invalid value

    Acceptable values for config types are any of:
        1. A Python primitive type that resolves to a Dagster config type
            (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
            :py:class:`~python:str`, or :py:class:`~python:list`).

        2. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.Float`,
            :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
            :py:data:`~dagster.StringSource`, :py:data:`~dagster.Any`,
            :py:class:`~dagster.Array`, :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`,
            :py:class:`~dagster.Selector`, :py:class:`~dagster.Shape`, or
            :py:class:`~dagster.Permissive`.

        3. A bare python dictionary, which will be automatically wrapped in
            :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
            according to the same rules.

        4. A bare python list of length one which itself is config type.
            Becomes :py:class:`Array` with list element as an argument.

        5. An instance of :py:class:`~dagster.Field`.
    """

    def __init__(self, original_root, current_value, stack, reason=None, **kwargs):
        self.original_root = original_root
        self.current_value = current_value
        self.stack = stack
        super(DagsterInvalidConfigDefinitionError, self).__init__(
            (
                "Error defining config. Original value passed: {original_root}. "
                "{stack_str}{current_value} "
                "cannot be resolved.{reason_str}" + CONFIG_ERROR_VERBIAGE
            ).format(
                original_root=repr(original_root),
                stack_str="Error at stack path :" + ":".join(stack) + ". " if stack else "",
                current_value=repr(current_value),
                reason_str=" Reason: {reason}.".format(reason=reason) if reason else "",
            ),
            **kwargs,
        )


class DagsterInvariantViolationError(DagsterError):
    """Indicates the user has violated a well-defined invariant that can only be enforced
    at runtime."""


class DagsterExecutionStepNotFoundError(DagsterError):
    """Thrown when the user specifies execution step keys that do not exist."""

    def __init__(self, *args, **kwargs):
        self.step_keys = check.list_param(kwargs.pop("step_keys"), "step_keys", str)
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterExecutionPlanSnapshotNotFoundError(DagsterError):
    """Thrown when an expected execution plan snapshot could not be found on a PipelineRun."""


class DagsterRunNotFoundError(DagsterError):
    """Thrown when a run cannot be found in run storage."""

    def __init__(self, *args, **kwargs):
        self.invalid_run_id = check.str_param(kwargs.pop("invalid_run_id"), "invalid_run_id")
        super(DagsterRunNotFoundError, self).__init__(*args, **kwargs)


class DagsterStepOutputNotFoundError(DagsterError):
    """Indicates that previous step outputs required for an execution step to proceed are not
    available."""

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop("step_key"), "step_key")
        self.output_name = check.str_param(kwargs.pop("output_name"), "output_name")
        super(DagsterStepOutputNotFoundError, self).__init__(*args, **kwargs)


@contextmanager
def raise_execution_interrupts() -> Iterator[None]:
    with raise_interrupts_as(DagsterExecutionInterruptedError):
        yield


@contextmanager
def user_code_error_boundary(
    error_cls: Type[DagsterUserCodeExecutionError],
    msg_fn: Callable[[], str],
    log_manager: Optional[DagsterLogManager] = None,
    **kwargs: object,
) -> Iterator[None]:
    """
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around any user code invoked by the framework. This ensures that all user
    errors are wrapped in an exception derived from DagsterUserCodeExecutionError,
    and that the original stack trace of the user error is preserved, so that it
    can be reported without confusing framework code in the stack trace, if a
    tool author wishes to do so.

    Examples:

    .. code-block:: python

        with user_code_error_boundary(
            # Pass a class that inherits from DagsterUserCodeExecutionError
            DagsterExecutionStepExecutionError,
            # Pass a function that produces a message
            "Error occurred during step execution"
        ):
            call_user_provided_function()

    """
    check.callable_param(msg_fn, "msg_fn")
    check.class_param(error_cls, "error_cls", superclass=DagsterUserCodeExecutionError)

    with raise_execution_interrupts():
        if log_manager:
            log_manager.begin_python_log_capture()
        try:
            yield
        except DagsterError as de:
            # The system has thrown an error that is part of the user-framework contract
            raise de
        except Exception as e:  # pylint: disable=W0703
            # An exception has been thrown by user code and computation should cease
            # with the error reported further up the stack
            raise error_cls(
                msg_fn(), user_exception=e, original_exc_info=sys.exc_info(), **kwargs
            ) from e
        finally:
            if log_manager:
                log_manager.end_python_log_capture()


class DagsterUserCodeExecutionError(DagsterError):
    """
    This is the base class for any exception that is meant to wrap an
    :py:class:`~python:Exception` thrown by user code. It wraps that existing user code.
    The ``original_exc_info`` argument to the constructor is meant to be a tuple of the type
    returned by :py:func:`sys.exc_info <python:sys.exc_info>` at the call site of the constructor.

    Users should not subclass this base class for their own exceptions and should instead throw
    freely from user code. User exceptions will be automatically wrapped and rethrown.
    """

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop("user_exception"), "user_exception", Exception)
        original_exc_info = check.tuple_param(kwargs.pop("original_exc_info"), "original_exc_info")

        check.invariant(original_exc_info[0] is not None)

        super(DagsterUserCodeExecutionError, self).__init__(args[0], *args[1:], **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, "user_exception", Exception)
        self.original_exc_info = original_exc_info

    @property
    def is_user_code_error(self) -> bool:
        return True


class DagsterTypeCheckError(DagsterUserCodeExecutionError):
    """Indicates an error in the op type system at runtime. E.g. a op receives an
    unexpected input, or produces an output that does not match the type of the output definition.
    """


class DagsterExecutionLoadInputError(DagsterUserCodeExecutionError):
    """Indicates an error occurred while loading an input for a step."""

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop("step_key"), "step_key")
        self.input_name = check.str_param(kwargs.pop("input_name"), "input_name")
        super(DagsterExecutionLoadInputError, self).__init__(*args, **kwargs)


class DagsterExecutionHandleOutputError(DagsterUserCodeExecutionError):
    """Indicates an error occurred while handling an output for a step."""

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop("step_key"), "step_key")
        self.output_name = check.str_param(kwargs.pop("output_name"), "output_name")
        super(DagsterExecutionHandleOutputError, self).__init__(*args, **kwargs)


class DagsterExecutionStepExecutionError(DagsterUserCodeExecutionError):
    """Indicates an error occurred while executing the body of an execution step."""

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop("step_key"), "step_key")
        self.op_name = check.str_param(kwargs.pop("op_name"), "op_name")
        self.op_def_name = check.str_param(kwargs.pop("op_def_name"), "op_def_name")
        super(DagsterExecutionStepExecutionError, self).__init__(*args, **kwargs)


class DagsterResourceFunctionError(DagsterUserCodeExecutionError):
    """
    Indicates an error occurred while executing the body of the ``resource_fn`` in a
    :py:class:`~dagster.ResourceDefinition` during resource initialization.
    """


class DagsterConfigMappingFunctionError(DagsterUserCodeExecutionError):
    """
    Indicates that an unexpected error occurred while executing the body of a config mapping
    function defined in a :py:class:`~dagster.JobDefinition` or `~dagster.GraphDefinition` during
    config parsing.
    """


class DagsterTypeLoadingError(DagsterUserCodeExecutionError):
    """
    Indicates that an unexpected error occurred while executing the body of an type load
    function defined in a :py:class:`~dagster.DagsterTypeLoader` during loading of a custom type.
    """


class DagsterTypeMaterializationError(DagsterUserCodeExecutionError):
    """
    Indicates that an unexpected error occurred while executing the body of an output
    materialization function defined in a :py:class:`~dagster.DagsterTypeMaterializer` during
    materialization of a custom type.
    """


class DagsterUnknownResourceError(DagsterError, AttributeError):
    # inherits from AttributeError as it is raised within a __getattr__ call... used to support
    # object hasattr method
    """Indicates that an unknown resource was accessed in the body of an execution step. May often
    happen by accessing a resource in the compute function of an op without first supplying the
    op with the correct `required_resource_keys` argument.
    """

    def __init__(self, resource_name, *args, **kwargs):
        self.resource_name = check.str_param(resource_name, "resource_name")
        msg = (
            "Unknown resource `{resource_name}`. Specify `{resource_name}` as a required resource "
            "on the compute / config function that accessed it."
        ).format(resource_name=resource_name)
        super(DagsterUnknownResourceError, self).__init__(msg, *args, **kwargs)


class DagsterInvalidInvocationError(DagsterError):
    """
    Indicates that an error has occurred when an op has been invoked, but before the actual
    core compute has been reached.
    """


class DagsterInvalidConfigError(DagsterError):
    """Thrown when provided config is invalid (does not type check against the relevant config
    schema)."""

    def __init__(self, preamble, errors, config_value, *args, **kwargs):
        from dagster._config import EvaluationError

        check.str_param(preamble, "preamble")
        self.errors = check.list_param(errors, "errors", of_type=EvaluationError)
        self.config_value = config_value

        error_msg = preamble
        error_messages = []

        for i_error, error in enumerate(self.errors):
            error_messages.append(error.message)
            error_msg += "\n    Error {i_error}: {error_message}".format(
                i_error=i_error + 1, error_message=error.message
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(DagsterInvalidConfigError, self).__init__(error_msg, *args, **kwargs)


class DagsterUnmetExecutorRequirementsError(DagsterError):
    """Indicates the resolved executor is incompatible with the state of other systems
    such as the :py:class:`~dagster._core.instance.DagsterInstance` or system storage configuration.
    """


class DagsterSubprocessError(DagsterError):
    """An exception has occurred in one or more of the child processes dagster manages.
    This error forwards the message and stack trace for all of the collected errors.
    """

    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.subprocess_error_infos = check.list_param(
            kwargs.pop("subprocess_error_infos"), "subprocess_error_infos", SerializableErrorInfo
        )
        super(DagsterSubprocessError, self).__init__(*args, **kwargs)


class DagsterUserCodeUnreachableError(DagsterError):
    """Dagster was unable to reach a user code server to fetch information about user code."""


class DagsterUserCodeProcessError(DagsterError):
    """An exception has occurred in a user code process that the host process raising this error
    was communicating with."""

    @staticmethod
    def from_error_info(error_info):
        from dagster._utils.error import SerializableErrorInfo

        check.inst_param(error_info, "error_info", SerializableErrorInfo)
        return DagsterUserCodeProcessError(
            error_info.to_string(), user_code_process_error_infos=[error_info]
        )

    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.user_code_process_error_infos = check.list_param(
            kwargs.pop("user_code_process_error_infos"),
            "user_code_process_error_infos",
            SerializableErrorInfo,
        )
        super(DagsterUserCodeProcessError, self).__init__(*args, **kwargs)


class DagsterMaxRetriesExceededError(DagsterError):
    """Raised when raise_on_error is true, and retries were exceeded, this error should be raised."""

    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.user_code_process_error_infos = check.list_param(
            kwargs.pop("user_code_process_error_infos"),
            "user_code_process_error_infos",
            SerializableErrorInfo,
        )
        super(DagsterMaxRetriesExceededError, self).__init__(*args, **kwargs)

    @staticmethod
    def from_error_info(error_info):
        from dagster._utils.error import SerializableErrorInfo

        check.inst_param(error_info, "error_info", SerializableErrorInfo)
        return DagsterMaxRetriesExceededError(
            error_info.to_string(), user_code_process_error_infos=[error_info]
        )


class DagsterRepositoryLocationNotFoundError(DagsterError):
    pass


class DagsterRepositoryLocationLoadError(DagsterError):
    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.load_error_infos = check.list_param(
            kwargs.pop("load_error_infos"),
            "load_error_infos",
            SerializableErrorInfo,
        )
        super(DagsterRepositoryLocationLoadError, self).__init__(*args, **kwargs)


class DagsterLaunchFailedError(DagsterError):
    """Indicates an error while attempting to launch a pipeline run."""

    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.serializable_error_info = check.opt_inst_param(
            kwargs.pop("serializable_error_info", None),
            "serializable_error_info",
            SerializableErrorInfo,
        )
        super(DagsterLaunchFailedError, self).__init__(*args, **kwargs)


class DagsterBackfillFailedError(DagsterError):
    """Indicates an error while attempting to launch a backfill."""

    def __init__(self, *args, **kwargs):
        from dagster._utils.error import SerializableErrorInfo

        self.serializable_error_info = check.opt_inst_param(
            kwargs.pop("serializable_error_info", None),
            "serializable_error_info",
            SerializableErrorInfo,
        )
        super(DagsterBackfillFailedError, self).__init__(*args, **kwargs)


class DagsterRunAlreadyExists(DagsterError):
    """Indicates that a pipeline run already exists in a run storage."""


class DagsterSnapshotDoesNotExist(DagsterError):
    """Indicates you attempted to create a pipeline run with a nonexistent snapshot id"""


class DagsterRunConflict(DagsterError):
    """Indicates that a conflicting pipeline run exists in a run storage."""


class DagsterTypeCheckDidNotPass(DagsterError):
    """Indicates that a type check failed.

    This is raised when ``raise_on_error`` is ``True`` in calls to the synchronous job and
    graph execution APIs (e.g. `graph.execute_in_process()`, `job.execute_in_process()` -- typically
    within a test), and a :py:class:`~dagster.DagsterType`'s type check fails by returning either
    ``False`` or an instance of :py:class:`~dagster.TypeCheck` whose ``success`` member is ``False``.
    """

    def __init__(self, description=None, metadata_entries=None, dagster_type=None):
        from dagster import DagsterType, MetadataEntry

        super(DagsterTypeCheckDidNotPass, self).__init__(description)
        self.description = check.opt_str_param(description, "description")
        self.metadata_entries = check.opt_list_param(
            metadata_entries, "metadata_entries", of_type=MetadataEntry
        )
        self.dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)


class DagsterEventLogInvalidForRun(DagsterError):
    """Raised when the event logs for a historical run are malformed or invalid."""

    def __init__(self, run_id):
        self.run_id = check.str_param(run_id, "run_id")
        super(DagsterEventLogInvalidForRun, self).__init__(
            "Event logs invalid for run id {}".format(run_id)
        )


class ScheduleExecutionError(DagsterUserCodeExecutionError):
    """Errors raised in a user process during the execution of schedule."""


class SensorExecutionError(DagsterUserCodeExecutionError):
    """Errors raised in a user process during the execution of a sensor (or its job)."""


class PartitionExecutionError(DagsterUserCodeExecutionError):
    """Errors raised during the execution of user-provided functions of a partition set schedule."""


class DagsterInvalidAssetKey(DagsterError):
    """Error raised by invalid asset key"""


class DagsterInvalidMetadata(DagsterError):
    """Error raised by invalid metadata parameters"""


class HookExecutionError(DagsterUserCodeExecutionError):
    """Error raised during the execution of a user-defined hook."""


class RunStatusSensorExecutionError(DagsterUserCodeExecutionError):
    """Error raised during the execution of a user-defined run status sensor."""


class FreshnessPolicySensorExecutionError(DagsterUserCodeExecutionError):
    """Error raised during the execution of a user-defined freshness policy sensor."""


class DagsterImportError(DagsterError):
    """Import error raised while importing user-code."""


class JobError(DagsterUserCodeExecutionError):
    """Errors raised during the execution of user-provided functions for a defined Job."""


class DagsterUnknownStepStateError(DagsterError):
    """When job execution completes with steps in an unknown state"""


class DagsterObjectStoreError(DagsterError):
    """Errors during an object store operation."""


class DagsterInvalidPropertyError(DagsterError):
    """Indicates that an invalid property was accessed. May often happen by accessing a property
    that no longer exists after breaking changes."""


class DagsterHomeNotSetError(DagsterError):
    """
    The user has tried to use a command that requires an instance or invoke DagsterInstance.get()
    without setting DAGSTER_HOME env var.
    """


class DagsterUnknownPartitionError(DagsterError):
    """
    The user has tried to access run config for a partition name that does not exist.
    """


class DagsterUndefinedLogicalVersionError(DagsterError):
    """
    The user attempted to retrieve the most recent logical version for an asset, but no logical version is defined.
    """
