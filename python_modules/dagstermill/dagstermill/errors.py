from dagster.core.errors import DagsterUserCodeExecutionError


class DagstermillError(Exception):
    pass


class DagstermillExecutionError(DagstermillError, DagsterUserCodeExecutionError):
    pass
