from enum import Enum


class SolidExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class SolidUserError(Exception):
    pass


class SolidInvalidDefinition(SolidUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''
    pass


class SolidTypeError(SolidUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class SolidExecutionError(SolidUserError):
    '''Indicates an error in user space code'''
    pass
