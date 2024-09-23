from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Generic, Mapping, Optional, TypeVar, cast

from dagster import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._serdes.serdes import PackableValue, deserialize_value, serialize_value

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


@contextmanager
def scoped_definitions_state(**state_objects: Any) -> Generator:
    """For test cases that involved state-backed definition objects. This context manager
    allows one to see backing state for a definitions object and test reconstruction
    logic.

    Examples:

    .. code-block:: python

        with scoped_definitions_state(test_key=ExampleDefState(a_string="bar")):
            loader_cached = ExampleStateBackedDefinitionsLoader("test_key")
            defs = loader_cached.build_defs()
            assert len(defs.get_all_asset_specs()) == 1
            assert defs.get_assets_def("bar")
    """
    ...


@contextmanager
def scoped_reconstruction_serdes_objects(
    state_objects: Optional[Mapping[str, Any]] = None,
) -> Generator:
    with scoped_reconstruction_metadata(
        {k: serialize_value(v) for k, v in state_objects.items()} if state_objects else None
    ):
        yield


@contextmanager
def scoped_reconstruction_metadata(
    reconstruction_metadata: Optional[Mapping[str, Any]] = None,
) -> Generator:
    prev_context = DefinitionsLoadContext.get()
    reconstruction_metadata = reconstruction_metadata or {}
    try:
        prev_load_data = prev_context._repository_load_data  # noqa
        DefinitionsLoadContext.set(
            DefinitionsLoadContext(
                load_type=DefinitionsLoadType.RECONSTRUCTION,
                repository_load_data=RepositoryLoadData(
                    cacheable_asset_data=prev_load_data.cacheable_asset_data
                    if prev_load_data
                    else {},
                    reconstruction_metadata={
                        **{
                            k: CodeLocationReconstructionMetadataValue(v)
                            for k, v in reconstruction_metadata.items()
                        },
                        **(prev_load_data.reconstruction_metadata if prev_load_data else {}),
                    },
                ),
            )
        )
        yield
    finally:
        DefinitionsLoadContext.set(prev_context)


def unwrapped_defs_metadata(defs: Definitions) -> Mapping[str, Any]:
    return {
        k: metadata_value.value
        for k, metadata_value in defs.metadata.items()
        if isinstance(metadata_value, CodeLocationReconstructionMetadataValue)
    }
