from dagster.core.errors import DagsterError, DagsterUserCodeExecutionError


class DagstermillError(DagsterError):
    """Base class for errors raised by dagstermill."""


class DagstermillExecutionError(DagstermillError, DagsterUserCodeExecutionError):
    """Errors raised during the execution of dagstermill solids."""
