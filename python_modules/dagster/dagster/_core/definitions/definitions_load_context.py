import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Optional, TypeVar, cast

from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from dagster_shared.serdes.serdes import PackableValue, deserialize_value, serialize_value

from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    AssetsDefinitionCacheableData,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
)
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._core.storage.defs_state.base import DefsStateStorage

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
        self._pending_reconstruction_metadata = {}

        defs_state_info = repository_load_data.defs_state_info if repository_load_data else None
        if load_type == DefinitionsLoadType.INITIALIZATION and defs_state_info is None:
            # defs_state_info is passed in during INITIALIZATION if explicit state versions
            # are provided via CLI arguments, otherwise we use the latest available state info
            state_storage = DefsStateStorage.get()
            self._defs_state_info = (
                state_storage.get_latest_defs_state_info() if state_storage else None
            )
        else:
            self._defs_state_info = defs_state_info

    @classmethod
    def get(cls) -> "DefinitionsLoadContext":
        """Get the current DefinitionsLoadContext. If it has not been set, the
        context is assumed to be in initialization, and the state versions are
        set to the latest available versions.
        """
        return DefinitionsLoadContext._instance or cls(load_type=DefinitionsLoadType.INITIALIZATION)

    @classmethod
    def set(cls, instance: "DefinitionsLoadContext") -> None:
        """Get the current DefinitionsLoadContext."""
        cls._instance = instance

    @classmethod
    def is_set(cls) -> bool:
        """bool: Whether the context has been set."""
        return cls._instance is not None

    @property
    def load_type(self) -> DefinitionsLoadType:
        """DefinitionsLoadType: Classifier for scenario in which Definitions are being loaded."""
        return self._load_type

    def add_to_pending_reconstruction_metadata(self, key: str, metadata: Any) -> None:
        self._pending_reconstruction_metadata[key] = metadata

    def get_pending_reconstruction_metadata(self) -> Mapping[str, Any]:
        return self._pending_reconstruction_metadata

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
            {
                k: v.data if isinstance(v, CodeLocationReconstructionMetadataValue) else v
                for k, v in self._repository_load_data.reconstruction_metadata.items()
            }
            if self._repository_load_data
            else {}
        )

    @property
    def defs_state_info(self) -> Optional[DefsStateInfo]:
        return self._defs_state_info

    def _get_defs_state_version(self, key: str) -> Optional[str]:
        """Ensures that if we attempt to access a key that doesn't exist, we mark it as None."""
        current_info = self._defs_state_info or DefsStateInfo.empty()
        version = current_info.get_version(key)
        if version is None:
            self._defs_state_info = DefsStateInfo.add_version(current_info, key, None)
        return version

    @contextmanager
    def temp_state_path(self, key: str) -> Iterator[Optional[Path]]:
        """Context manager that creates a temporary path to hold local state for a component."""
        state_storage = DefsStateStorage.get()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                "Attempted to get a temp state path without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )
        # if no state has ever been written for this key, we return None to indicate that no state is available
        version = self._get_defs_state_version(key)
        if version is None:
            yield None
            return
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / key
            state_storage.download_state_to_path(key, version, state_path)
            yield state_path


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

    def get_or_fetch_state(self) -> TState:
        context = DefinitionsLoadContext.get()
        state = (
            cast("TState", deserialize_value(context.reconstruction_metadata[self.defs_key]))
            if (
                context.load_type == DefinitionsLoadType.RECONSTRUCTION
                and self.defs_key in context.reconstruction_metadata
            )
            else self.fetch_state()
        )
        context.add_to_pending_reconstruction_metadata(self.defs_key, serialize_value(state))

        return state

    def build_defs(self) -> Definitions:
        state = self.get_or_fetch_state()

        return self.defs_from_state(state).with_reconstruction_metadata(
            {self.defs_key: serialize_value(state)}
        )
