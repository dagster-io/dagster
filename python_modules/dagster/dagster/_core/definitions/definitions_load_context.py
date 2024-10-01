from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Mapping, Optional, Sequence, TypeVar, cast

from dagster._core.definitions.cacheable_assets import AssetsDefinitionCacheableData
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvariantViolationError
from dagster._serdes.serdes import PackableValue, deserialize_value, serialize_value

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

    @property
    def cacheable_asset_data(self) -> Mapping[str, Sequence[AssetsDefinitionCacheableData]]:
        """Sequence[AssetDefinitionCacheableData]: A sequence of cacheable asset data created
        during code location initialization. Accessing this during initialization will raise an
        error.
        """
        if self._load_type == DefinitionsLoadType.INITIALIZATION:
            raise DagsterInvariantViolationError(
                "Attempted to access cacheable asset data during code location initialization."
                " Cacheable asset data is only available during reconstruction of a code location."
            )
        return self._repository_load_data.cacheable_asset_data if self._repository_load_data else {}

    @cached_property
    def reconstruction_metadata(self) -> Mapping[str, Any]:
        """Mapping[str, Any]: A dictionary containing metadata from the returned Definitions object
        at initial code location initialization. Accessing this during initialization will raise an
        error.
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


TState = TypeVar("TState", bound=PackableValue)


class StateBackedDefinitionsLoader(ABC, Generic[TState]):
    """A class for building state-backed definitions. In a structured way. It
    handles manipulation of the DefinitionsLoadContext on the user's behalf.

    The goal here is so that an unreliable backing source is fetched only
    at code server load time, which defines the code location. When, for example,
    a run worker is launched, the backing source is not queryed again, and
    only `defs_from_state` is called.

    Current meant for internal usage only hence TState must be a marked as whitelist_for_serdes.

    Args:
        defs_key (str): The unique key for the definitions. Must be unique per code location.

    Examples:

    .. code-block:: python

        @whitelist_for_serdes
        @record
        class ExampleDefState:
            a_string: str

        class ExampleStateBackedDefinitionsLoader(StateBackedDefinitionsLoader[ExampleDefState]):
            def fetch_state(self) -> ExampleDefState:
                # Fetch from potentially unreliable API (e.g. Rest API)
                return ExampleDefState(a_string="foo")

            def defs_from_state(self, state: ExampleDefState) -> Definitions:
                # Construct or reconstruct the Definitions from the previously
                # fetched state.
                return Definitions([AssetSpec(key=state.a_string)])
    """

    @property
    @abstractmethod
    def defs_key(self) -> str:
        """The unique key for the definitions. Must be unique per code location."""
        ...

    @abstractmethod
    def fetch_state(self) -> TState:
        """Subclasses must implement this method. This is where the integration runs
        code that fetches the backing state from the source of truth for the definitions.
        This is only called when the code location is initializing, for example on
        code server load, or when loading via dagster dev.
        """
        ...

    @abstractmethod
    def defs_from_state(self, state: TState) -> Definitions:
        """Subclasses must implement this method. It is invoked whenever the code location
        is loading, whether it be initializaton or reconstruction. In the case of
        intialization, it takes the result of fetch_backing state that just happened.
        When reconstructing, it takes the state that was previously fetched and attached
        as metadata.

        This method also takes responsibility for attaching the state to the definitions
        on its metadata, with the key passed in as defs_key.
        """
        ...

    def build_defs(self) -> Definitions:
        context = DefinitionsLoadContext.get()

        state = (
            cast(TState, deserialize_value(context.reconstruction_metadata[self.defs_key]))
            if (
                context.load_type == DefinitionsLoadType.RECONSTRUCTION
                and self.defs_key in context.reconstruction_metadata
            )
            else self.fetch_state()
        )

        return self.defs_from_state(state).with_reconstruction_metadata(
            {self.defs_key: serialize_value(state)}
        )
