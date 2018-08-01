from enum import Enum

from dagster import check


class DagsterExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class DagsterError(Exception):
    pass


class DagsterUserError(DagsterError):
    pass


class DagsterInvalidDefinitionError(DagsterUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''
    pass


class DagsterInvariantViolationError(DagsterUserError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''
    pass


class DagsterTypeError(DagsterUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class DagsterUserCodeExecutionError(DagsterUserError):
    '''Indicates that user space code has raised an error'''

    def __init__(self, *args, user_exception, original_exc_info, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        super().__init__(*args, **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info


class DagsterExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, execution_result, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXME: need to reorganize to fix this circular dep
        # Probable fix is to move all "execution result" objects
        # to definitions
        import dagster.core.execution
        self.execution_result = check.inst_param(
            execution_result,
            'execution_result',
            dagster.core.execution.SolidExecutionResult,
        )
