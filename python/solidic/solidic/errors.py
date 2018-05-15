from enum import Enum

import check

import solidic.definitions


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


class SolidTypeError(SolidUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class SolidExecutionError(SolidUserError):
    '''Indicates an error in user space code'''

    def __init__(self, *args, user_exception=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)


class SolidExpectationFailedError(SolidError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, *args, failed_expectation_results, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_results = check.list_param(
            failed_expectation_results,
            'failed_expectation_results',
            # fully qualified name prevents circular reference
            solidic.definitions.SolidExpectationResult
        )
