'''Dagster error classes.

All errors thrown by the Dagster framework inherit from :class:`DagsterError <dagster.DagsterError>`.
Users should not subclass this base class for their own exceptions.

There is another exception base class,
:class:`DagsterUserCodeExecutionError <dagster.DagsterUserCodeExecutionError>`, which is meant to
be used in concert with the :func:`dagster.core.errors.user_code_error_boundary`. Dagster calls into
user code which can be arbitrary computation and can itself throw. The pattern here is to use the
error boundary to catch this exception, and then rethrow that exception wrapped in a
:class:`DagsterUserCodeExecutionError <dagster.DagsterUserCodeExecutionError>`-derived exception.
This new exception is there to embellish the original error with additional context that the
Dagster runtime is aware of.
'''

import sys
import traceback
from contextlib import contextmanager

from future.utils import raise_from

from dagster import check


class DagsterError(Exception):
    '''Base class for all errors thrown by the Dagster framework.

    Users should not subclass this base class for their own exceptions.'''

    @property
    def is_user_code_error(self):
        '''Returns true if this error is attributable to user code.'''
        return False


class DagsterInvalidDefinitionError(DagsterError):
    '''Indicates that the rules for a definition have been violated by the user.'''


CONFIG_ERROR_VERBIAGE = '''
This value can be a:
    - Field
    - Python primitive types that resolve to dagster config types
        - int, float, bool, str, list.
    - A dagster config type: Int, Float, Bool, List, Optional, Selector, Dict
    - A bare python dictionary, which is wrapped in Field(Dict(...)). Any values
      in the dictionary get resolved by the same rules, recursively.
    - A python list with a single entry that can resolve to a type, e.g. [int]
'''


class DagsterInvalidConfigDefinitionError(DagsterError):
    '''Indicates that you have attempted to construct a config with an invalid value

    This value can be a:

        - :py:class:`Field`
        - Python primitive types that resolve to dagster config types
            - int, float, bool, str, list.
        - A dagster config type: Int, Float, Bool, List, Optional, :py:class:`Selector`, :py:class:`Dict`
        - A bare python dictionary, which is wrapped in Field(Dict(...)). Any values
          in the dictionary get resolved by the same rules, recursively.
        - A python list with a single entry that can resolve to a type, e.g. [int]
    '''

    def __init__(self, original_root, current_value, stack, reason=None, **kwargs):
        self.original_root = original_root
        self.current_value = current_value
        self.stack = stack
        super(DagsterInvalidConfigDefinitionError, self).__init__(
            (
                'Error defining config. Original value passed: {original_root}. '
                '{stack_str}{current_value} '
                'cannot be resolved.{reason_str}' + CONFIG_ERROR_VERBIAGE
            ).format(
                original_root=repr(original_root),
                stack_str='Error at stack path :' + ':'.join(stack) + '. ' if stack else '',
                current_value=repr(current_value),
                reason_str=' Reason: {reason}.'.format(reason=reason) if reason else '',
            ),
            **kwargs
        )


class DagsterInvariantViolationError(DagsterError):
    '''Indicates the user has violated a well-defined invariant that can only be enforced
    at runtime.'''


class DagsterExecutionStepNotFoundError(DagsterError):
    '''Thrown when the user specifies execution step keys that do not exist.'''

    def __init__(self, *args, **kwargs):
        self.step_keys = check.list_param(kwargs.pop('step_keys'), 'step_keys', str)
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterRunNotFoundError(DagsterError):
    '''Thrown when re-execution is attempted but the original run cannot be found.'''

    def __init__(self, *args, **kwargs):
        self.invalid_run_id = check.str_param(kwargs.pop('invalid_run_id'), 'invalid_run_id')
        super(DagsterRunNotFoundError, self).__init__(*args, **kwargs)


class DagsterStepOutputNotFoundError(DagsterError):
    '''Indicates that previous step outputs required for an execution step to proceed are not
    available.'''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        self.output_name = check.str_param(kwargs.pop('output_name'), 'output_name')
        super(DagsterStepOutputNotFoundError, self).__init__(*args, **kwargs)


def _add_inner_exception_for_py2(msg, exc_info):
    if sys.version_info[0] == 2:
        return (
            msg
            + '\n\nThe above exception was the direct cause of the following exception:\n\n'
            + ''.join(traceback.format_exception(*exc_info))
        )

    return msg


@contextmanager
def user_code_error_boundary(error_cls, msg_fn, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in an exception derived from DagsterUserCodeExecutionError,
    and that the original stack trace of the user error is preserved, so that it
    can be reported without confusing framework code in the stack trace, if a
    tool author wishes to do so. This has been especially help in a notebooking
    context.


    Examples:

    .. code-block:: python

        with user_code_error_boundary(
            # Pass a class that inherits from DagsterUserCodeExecutionError
            DagstermillExecutionError,
            # Pass a function that produces a message
            lambda: 'Error occurred during the execution of Dagstermill solid '
            '{solid_name}: {notebook_path}'.format(
                solid_name=name, notebook_path=notebook_path
            ),
        ):
            call_user_provided_function()

    '''
    check.callable_param(msg_fn, 'msg_fn')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    try:
        yield
    except DagsterError as de:
        # The system has thrown an error that is part of the user-framework contract
        raise de
    except Exception as e:  # pylint: disable=W0703
        # An exception has been thrown by user code and computation should cease
        # with the error reported further up the stack
        raise_from(
            error_cls(msg_fn(), user_exception=e, original_exc_info=sys.exc_info(), **kwargs), e
        )


class DagsterUserCodeExecutionError(DagsterError):
    '''
    This is the base class for any exception that is meant to wrap an
    :class:`Exception <python:Exception>` thrown by user code. It wraps that existing user code.
    The ``original_exc_info`` argument to the constructor is meant to be a tuple of the type
    returned by :func:`sys.exc_info <python:sys.exc_info>` at the call site of the constructor.
    '''

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop('user_exception'), 'user_exception', Exception)
        original_exc_info = check.tuple_param(kwargs.pop('original_exc_info'), 'original_exc_info')

        check.invariant(original_exc_info[0] is not None)

        msg = _add_inner_exception_for_py2(args[0], original_exc_info)

        super(DagsterUserCodeExecutionError, self).__init__(msg, *args[1:], **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info

    @property
    def is_user_specified_failure(self):
        from dagster.core.definitions.events import Failure

        return isinstance(self.user_exception, Failure)

    @property
    def user_specified_failure(self):
        check.invariant(
            self.is_user_specified_failure,
            (
                'Can only call if user-specified failure (i.e. the user threw '
                'an explicit Failure event in user-code'
            ),
        )
        return self.user_exception

    @property
    def is_user_code_error(self):
        return True


class DagsterTypeCheckError(DagsterUserCodeExecutionError):
    '''Indicates an error in the solid type system at runtime. E.g. a solid receives an
    unexpected input, or produces an output that does not match the type of the output definition.
    '''


class DagsterExecutionStepExecutionError(DagsterUserCodeExecutionError):
    '''Indicates an error occured while executing the body of an execution step.'''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        self.solid_name = check.str_param(kwargs.pop('solid_name'), 'solid_name')
        self.solid_def_name = check.str_param(kwargs.pop('solid_def_name'), 'solid_def_name')
        super(DagsterExecutionStepExecutionError, self).__init__(*args, **kwargs)


class DagsterResourceFunctionError(DagsterUserCodeExecutionError):
    '''
    Indicates an error occured while executing the body of the ``resource_fn`` in a
    :class:`ResourceDefinition <dagster.ResourceDefinition>` during resource initialization.
    '''


class DagsterConfigMappingFunctionError(DagsterUserCodeExecutionError):
    '''
    Indicates that an unexpected error occured while executing the body of a config mapping
    function defined in a :class:`CompositeSolidDefinition <dagster.CompositeSolidDefinition>`
    during config parsing.
    '''


class DagsterInputHydrationConfigError(DagsterUserCodeExecutionError):
    '''
    Indicates that an unexpected error occurred while executing the body of an input hydration
    config function defined in a :class:`InputHydrationConfig <dagster.InputHydrationConfig>` during
    input hydration of a custom type
    '''


class DagsterOutputMaterializationError(DagsterUserCodeExecutionError):
    '''
    Indicates that an unexpected error occurred while executing the body of an output
    materialization function defined in a
    :class:`OutputMaterializationConfig <dagster.OutputMaterializationConfig>` during output
    materialization of a custom type
    '''


class DagsterUnknownResourceError(DagsterError, AttributeError):
    # inherits from AttributeError as it is raised within a __getattr__ call... used to support
    # object hasattr method
    ''' Indicates that an unknown resource was accessed in the body of an execution step. May often
    happen by accessing a resource in the compute function of a solid without first supplying the
    solid with the correct `required_resource_keys` argument.
    '''

    def __init__(self, resource_name, *args, **kwargs):
        self.resource_name = check.str_param(resource_name, 'resource_name')
        msg = (
            'Unknown resource `{resource_name}. Specify `{resource_name}` as a required resource '
            'on the compute / config function that accessed it.'
        ).format(resource_name=resource_name)
        super(DagsterUnknownResourceError, self).__init__(msg, *args, **kwargs)


class DagsterInvalidConfigError(DagsterError):
    '''Thrown when provided config is invalid (does not type check against the relevant config
    schema).'''

    def __init__(self, preamble, errors, config_value, *args, **kwargs):
        from dagster.config.errors import (
            friendly_string_for_error,
            EvaluationError,
        )

        check.str_param(preamble, 'preamble')
        self.errors = check.list_param(errors, 'errors', of_type=EvaluationError)
        self.config_value = config_value

        error_msg = preamble
        error_messages = []

        for i_error, error in enumerate(self.errors):
            error_message = friendly_string_for_error(error)
            error_messages.append(error_message)
            error_msg += '\n    Error {i_error}: {error_message}'.format(
                i_error=i_error + 1, error_message=error_message
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(DagsterInvalidConfigError, self).__init__(error_msg, *args, **kwargs)


class DagsterUnmetExecutorRequirementsError(DagsterError):
    '''Indicates the resolved executor is incompatible with the state of other systems
    such as the :class:`DagsterInstance <dagster.DagsterInstance>` or system storage configuration.
    '''


class DagsterSubprocessError(DagsterError):
    '''An exception has occurred in one or more of the child processes dagster manages.
    This error forwards the message and stack trace for all of the collected errors.
    '''

    def __init__(self, *args, **kwargs):
        from dagster.utils.error import SerializableErrorInfo

        self.subprocess_error_infos = check.list_param(
            kwargs.pop('subprocess_error_infos'), 'subprocess_error_infos', SerializableErrorInfo
        )
        super(DagsterSubprocessError, self).__init__(*args, **kwargs)


class DagsterLaunchFailedError(DagsterError):
    '''Indicates an error while attempting to launch a pipeline run.
    '''


class DagsterInstanceMigrationRequired(DagsterError):
    '''Indicates that the dagster instance must be migrated.'''

    def __init__(self, msg=None, db_revision=None, head_revision=None):
        super(DagsterInstanceMigrationRequired, self).__init__(
            'Instance is out of date and must be migrated{additional_msg}.'
            '{revision_clause} Please run `dagster instance migrate`.'.format(
                additional_msg=' ({msg})'.format(msg=msg) if msg else '',
                revision_clause=(
                    ' Database is at revision {db_revision}, head is '
                    '{head_revision}.'.format(db_revision=db_revision, head_revision=head_revision)
                    if db_revision or head_revision
                    else ''
                ),
            )
        )


class DagsterRunAlreadyExists(DagsterError):
    '''Indicates that a pipeline run already exists in a run storage.'''


class DagsterRunConflict(DagsterError):
    '''Indicates that a conflicting pipeline run exists in a run storage.'''
