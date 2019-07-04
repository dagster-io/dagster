'''
Errors in Dagster:

All errors thrown by the Dagster framework inherit from DagsterError. Users should not inherit their
own exceptions from DagsterError. This how dagster communicates errors like definition errors and
invariant violations.

There is another exception base class, DagsterUserCodeExecutionError, which is meant to be used in
concert with the user_code_error_boundary. Dagster calls into user code which can be arbitrary
computation and can itself throw. The pattern here is to use the error boundary to catch this
exception, and then rethrow that exception wrapped in a DagsterUserCodeExecutionError-derived
exception. This new exception is there to embellish the original error with additional context that
the dagster runtime is aware of.
'''

from contextlib import contextmanager
from future.utils import raise_from

import sys
import traceback

from dagster import check


class DagsterError(Exception):
    @property
    def is_user_code_error(self):
        return False


class DagsterInvalidDefinitionError(DagsterError):
    '''Indicates that some violation of the definition rules has been violated by the user'''


class DagsterInvariantViolationError(DagsterError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''


class DagsterExecutionStepNotFoundError(DagsterError):
    '''
    Throw when the user specifies an execution step key that does not exist.
    '''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterRunNotFoundError(DagsterError):
    def __init__(self, *args, **kwargs):
        self.invalid_run_id = check.str_param(kwargs.pop('invalid_run_id'), 'invalid_run_id')
        super(DagsterRunNotFoundError, self).__init__(*args, **kwargs)


class DagsterStepOutputNotFoundError(DagsterError):
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


    Example:

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
    This is the base class for any exception that is meant to wrap an Exception thrown by user code.
    It wraps that existing user code. The original_exc_info argument to the ctor is meant to be a
    sys.exc_info at the site of constructor.
    '''

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop('user_exception'), 'user_exception', Exception)
        original_exc_info = check.tuple_param(kwargs.pop('original_exc_info'), 'original_exc_info')

        if original_exc_info[0] is None:
            raise Exception('bad dude {}'.format(type(self)))

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
    '''Indicates an error occured during the body of execution step execution'''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        self.solid_name = check.str_param(kwargs.pop('solid_name'), 'solid_name')
        self.solid_def_name = check.str_param(kwargs.pop('solid_def_name'), 'solid_def_name')
        super(DagsterExecutionStepExecutionError, self).__init__(*args, **kwargs)


class DagsterResourceFunctionError(DagsterUserCodeExecutionError):
    '''Indicates an error occured during the body of resource_fn in a ResourceDefinition'''


class DagsterInvalidConfigError(DagsterError):
    def __init__(self, pipeline, errors, config_value, *args, **kwargs):
        from dagster.core.definitions import PipelineDefinition
        from dagster.core.types.evaluator.errors import friendly_string_for_error, EvaluationError

        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.errors = check.list_param(errors, 'errors', of_type=EvaluationError)

        self.config_value = config_value

        error_msg = 'Pipeline "{pipeline}" config errors:'.format(pipeline=pipeline.name)

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
