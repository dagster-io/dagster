import warnings
from abc import ABC
from typing import Any, Mapping, Optional, Sequence

from dagster import (
    Failure
)


class DagsterSdfError(Failure, ABC):
    """The base exception of the ``dagster-sdf`` library."""

class DagsterSdfCliRuntimeError(DagsterSdfError, ABC):
    """Represents an error while executing an sdf CLI command."""

    def __init__(
        self,
        description: str,
        logs: Optional[Sequence[Mapping[str, Any]]] = None,
        raw_output: Optional[str] = None,
        messages: Optional[Sequence[str]] = None,
    ):
        if logs is not None:
            warnings.warn(
                "`logs` is a deprecated argument to DagsterSdfCliRuntimeError and will be discarded"
            )
        if raw_output is not None:
            warnings.warn(
                "`raw_output` is a deprecated argument to DagsterSdfCliRuntimeError and will be"
                " discarded"
            )
        metadata = {"Parsed CLI Messages": "\n".join(messages or [])}
        super().__init__(description, metadata=metadata)

class DagsterSdfInformationSchemaNotFoundError(DagsterSdfError):
    """Error when we expect the sdf information schema to have been generated already but it is absent."""

class DagsterSdfWorkspaceNotFoundError(DagsterSdfError):
    """Error when the specified workspace directory can not be found."""

class DagsterSdfWorkspaceYmlFileNotFoundError(DagsterSdfError):
    """Error when a workspace.sdf.yml file can not be found in the specified project directory."""