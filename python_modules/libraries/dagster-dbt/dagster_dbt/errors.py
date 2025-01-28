from abc import ABC

from dagster import DagsterInvariantViolationError, Failure


class DagsterDbtError(Failure, ABC):
    """The base exception of the ``dagster-dbt`` library."""


class DagsterDbtCliRuntimeError(DagsterDbtError, ABC):
    """Represents an error while executing a dbt CLI command."""


class DagsterDbtCloudJobInvariantViolationError(DagsterDbtError, DagsterInvariantViolationError):
    """Represents an error when a dbt Cloud job is not supported by the ``dagster-dbt`` library."""


class DagsterDbtProjectNotFoundError(DagsterDbtError):
    """Error when the specified project directory can not be found."""


class DagsterDbtProfilesDirectoryNotFoundError(DagsterDbtError):
    """Error when the specified profiles directory can not be found."""


class DagsterDbtManifestNotFoundError(DagsterDbtError):
    """Error when we expect manifest.json to generated already but it is absent."""


class DagsterDbtProjectYmlFileNotFoundError(DagsterDbtError):
    """Error when a dbt_project.yml file can not be found in the specified project directory."""
