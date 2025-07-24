from dagster._annotations import public
from dagster_shared.error import DagsterError


@public
class DagstermillError(DagsterError):
    """Base class for errors raised by dagstermill."""
