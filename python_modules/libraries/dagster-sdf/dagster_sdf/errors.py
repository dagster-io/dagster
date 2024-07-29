from abc import ABC

from dagster import Failure


class DagsterSdfError(Failure, ABC):
    """The base exception of the ``dagster-sdf`` library."""


class DagsterSdfCliRuntimeError(DagsterSdfError, ABC):
    """Represents an error while executing an sdf CLI command."""


class DagsterSdfInformationSchemaNotFoundError(DagsterSdfError):
    """Error when we expect the sdf information schema to have been generated already but it is absent."""


class DagsterSdfWorkspaceNotFoundError(DagsterSdfError):
    """Error when the specified workspace directory can not be found."""


class DagsterSdfWorkspaceYmlFileNotFoundError(DagsterSdfError):
    """Error when a workspace.sdf.yml file can not be found in the specified project directory."""
