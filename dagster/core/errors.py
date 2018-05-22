from enum import Enum

from dagster import check

import dagster.core.definitions


class SolidExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class SolidError(Exception):
    pass


class SolidUserError(SolidError):
    pass


class SolidInvalidDefinition(SolidUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''
    pass


class SolidInvariantViolation(SolidUserError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''
    pass


class SolidTypeError(SolidUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class SolidUserCodeExecutionError(SolidUserError):
    '''Indicates that user space code has raised an error'''

    def __init__(self, *args, user_exception, original_exc_info, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        super().__init__(*args, **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info


class SolidExpectationFailedError(SolidError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, *args, failed_expectation_results, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_results = check.list_param(
            failed_expectation_results,
            'failed_expectation_results',
            # fully qualified name prevents circular reference
            dagster.core.definitions.SolidExpectationResult
        )
