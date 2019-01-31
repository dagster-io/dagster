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


class DagsterRuntimeCoercionError(DagsterError):
    '''Runtime checked faild'''


class DagsterInvalidDefinitionError(DagsterUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''


class DagsterInvariantViolationError(DagsterUserError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''


class DagsterTypeError(DagsterUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''


class DagsterUserCodeExecutionError(DagsterUserError):
    '''Indicates that user space code has raised an error'''

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop('user_exception'), 'user_exception', Exception)
        original_exc_info = check.opt_tuple_param(
            kwargs.pop('original_exc_info', None), 'original_exc_info'
        )
        super(DagsterUserCodeExecutionError, self).__init__(*args, **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info


class DagsterExecutionStepNotFoundError(DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterUnmarshalInputNotFoundError(DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.input_name = check.str_param(kwargs.pop('input_name'), 'input_name')
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterUnmarshalInputNotFoundError, self).__init__(*args, **kwargs)


class DagsterUnmarshalInputError(DagsterUserCodeExecutionError):
    '''Indicates an error doing marshalling a specific input'''

    def __init__(self, *args, **kwargs):
        self.input_name = check.str_param(kwargs.pop('input_name'), 'input_name')
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterUnmarshalInputError, self).__init__(*args, **kwargs)


class DagsterMarshalOutputNotFoundError(DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.output_name = check.str_param(kwargs.pop('output_name'), 'output_name')
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterMarshalOutputNotFoundError, self).__init__(*args, **kwargs)


class DagsterMarshalOutputError(DagsterUserCodeExecutionError):
    '''Indicates an error doing marshalling on a specific output'''

    def __init__(self, *args, **kwargs):
        self.output_name = check.str_param(kwargs.pop('output_name'), 'output_name')
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterMarshalOutputError, self).__init__(*args, **kwargs)


class DagsterExecutionStepExecutionError(DagsterUserCodeExecutionError):
    pass


class DagsterInvalidSubplanExecutionError(DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.pipeline_name = check.str_param(kwargs.pop('pipeline_name'), 'pipeline_name')
        self.step_keys = check.list_param(kwargs.pop('step_keys'), 'step_keys', of_type=str)
        self.input_name = check.str_param(kwargs.pop('input_name'), 'input_name')
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')

        super(DagsterInvalidSubplanExecutionError, self).__init__(*args, **kwargs)


class DagsterExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, info, value, *args, **kwargs):
        super(DagsterExpectationFailedError, self).__init__(*args, **kwargs)
        self.info = info
        self.value = value

    def __repr__(self):
        inout_def = self.info.inout_def
        return (
            'DagsterExpectationFailedError('
            + 'solid={name}, '.format(name=self.info.solid.name)
            + '{key}={name}, '.format(key=inout_def.descriptive_key, name=inout_def.name)
            + 'expectation={name}'.format(name=self.info.expectation_def.name)
            + 'value={value}'.format(value=repr(self.value))
            + ')'
        )

    def __str__(self):
        return self.__repr__()
