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


class DagsterEvaluateValueError(DagsterError):
    '''Indicates that invalid value was passed to a type's evaluate_value method'''
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

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = kwargs.pop('user_exception', None)
        original_exc_info = kwargs.pop('original_exc_info', None)
        super(DagsterUserCodeExecutionError, self).__init__(*args, **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info


class DagsterExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, info, value, *args, **kwargs):
        super(DagsterExpectationFailedError, self).__init__(*args, **kwargs)
        self.info = info
        self.value = value

    def __repr__(self):
        inout_def = self.info.inout_def
        return (
            'DagsterExpectationFailedError(' +
            'solid={name}, '.format(name=self.info.solid_def.name) +
            '{key}={name}, '.format(key=inout_def.descriptive_key, name=inout_def.name) +
            'expectation={name}'.format(name=self.info.expectation_def.name
                                        ) + 'value={value}'.format(value=repr(self.value)) + ')'
        )

    def __str__(self):
        return self.__repr__()
