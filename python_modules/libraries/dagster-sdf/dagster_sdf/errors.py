from abc import ABC

from dagster import Failure


class DagsterSdfError(Failure, ABC):
    """The base exception of the ``dagster-sdf`` library."""


class DagsterSdfCliRuntimeError(DagsterSdfError, ABC):
    """Represents an error while executing an sdf CLI command."""
