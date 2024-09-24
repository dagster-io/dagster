from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Mapping, Optional

from dagster._core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryLoadData


class DefinitionsLoadType(Enum):
    """An enum that defines the different scenarios in which a Definitions object may be
    instantiated.

    When booting a Dagster process that contains definitions, one of two things are happening.

    1. `INITIALIZATION`: You are defining a set of definitions for Dagster to ingest, effectively updating Dagster's
        understanding of the world at a point in time.
    2. `RECONSTRUCTION`: You are reconstructing a set of definitions that were previously defined.

    This distinction is important when the source of truth for a Dagster definition is state
    (for example in a hosted ingestion or BI tool accessable via an API). The state should
    only be accessed when defining definitions, whereas when reconstructing definitions that
    state should be retrieved from Dagster's metastore.
    """

    INITIALIZATION = "INITIALIZATION"
    RECONSTRUCTION = "RECONSTRUCTION"


class DefinitionsLoadContext:
    """Holds data that's made available to Definitions-loading code when a DefinitionsLoader is
    invoked.
    User construction of this object is not supported.
    """

    _instance: ClassVar[Optional["DefinitionsLoadContext"]] = None

    def __init__(
        self,
        load_type: DefinitionsLoadType,
        repository_load_data: Optional["RepositoryLoadData"] = None,
    ):
        self._load_type = load_type
        self._repository_load_data = repository_load_data

    @classmethod
    def get(cls) -> "DefinitionsLoadContext":
        """Get the current DefinitionsLoadContext. If it has not been set, the
        context is assumed to be initialization.
        """
        return DefinitionsLoadContext._instance or cls(load_type=DefinitionsLoadType.INITIALIZATION)

    @classmethod
    def set(cls, instance: "DefinitionsLoadContext") -> None:
        """Get the current DefinitionsLoadContext."""
        cls._instance = instance

    @property
    def load_type(self) -> DefinitionsLoadType:
        """DefinitionsLoadType: Classifier for scenario in which Definitions are being loaded."""
        return self._load_type

    @cached_property
    def reconstruction_metadata(self) -> Mapping[str, Any]:
        """Mapping[str, Any]: A dictionary containing metadata from the returned Definitions object
        at initial code location construction. This will be empty in the code server process, but in
        child processes contain the metadata returned in the code server process.
        """
        if self._load_type == DefinitionsLoadType.INITIALIZATION:
            raise DagsterInvariantViolationError(
                "Attempted to access code location metadata during code location initialization."
                " Code location metadata is only available during reconstruction of a code location."
            )
        # Expose the wrapped metadata values so that users access exactly what they put in.
        return (
            {k: v.data for k, v in self._repository_load_data.reconstruction_metadata.items()}
            if self._repository_load_data
            else {}
        )
