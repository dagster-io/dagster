from dagster.core.errors import DagsterUserCodeExecutionError


class DagstermillError(Exception):
    '''Base class for errors raised by dagstermill.'''


class DagstermillExecutionError(DagstermillError, DagsterUserCodeExecutionError):
    '''Errors raised during the execution of dagstermill solids.'''
