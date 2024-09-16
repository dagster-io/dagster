from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Union

from typing_extensions import TypeAlias

from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.decorators.op_decorator import is_context_provided
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryLoadData

DefinitionsLoadFn: TypeAlias = Union[
    Callable[["DefinitionsLoadContext"], Definitions],
    Callable[[], Definitions],
]


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

    def __init__(
        self,
        load_type: DefinitionsLoadType,
        repository_load_data: Optional["RepositoryLoadData"] = None,
    ):
        self._load_type = load_type
        self._repository_load_data = repository_load_data

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


@record
class DefinitionsLoader:
    """An object that can be invoked to load a set of definitions."""

    load_fn: DefinitionsLoadFn

    @property
    def has_context_param(self) -> bool:
        return is_context_provided(get_function_params(self.load_fn))

    def __call__(self, context: Optional[DefinitionsLoadContext] = None) -> Definitions:
        """Load a set of definitions using the load_fn provided at construction time.

        Args:
            context (Optional[DefinitionsLoadContext]): If the load_fn requires a context object,
                this object must be provided. If the load_fn does not require a context object,
                this object must be None.

        Returns:
            Definitions: The loaded definitions.
        """
        if self.has_context_param:
            if context is None:
                raise DagsterInvalidInvocationError(
                    "Invoked a DefinitionsLoader that requires a DefinitionsLoadContext without providing one."
                )
            result = self.load_fn(context)  # type: ignore  # (has_context_param type-checker illegible)
        else:
            if context is not None:
                raise DagsterInvalidInvocationError(
                    "Passed a DefinitionsLoadContext to a DefinitionsLoader that does not accept one."
                )
            result = self.load_fn()  # type: ignore  # (has_context_param type-checker illegible)
        if not isinstance(result, Definitions):
            raise DagsterInvariantViolationError(
                "DefinitionsLoader must return a Definitions object"
            )
        return result
