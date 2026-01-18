from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Optional, TypeVar

from dagster_shared.serdes import serialize_value

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
    RepositoryLoadData,
)
from dagster.components.definitions import (
    LazyDefinitions as LazyDefinitions,
    definitions as definitions,
)

T_Defs = TypeVar("T_Defs", Definitions, RepositoryDefinition)


@contextmanager
def scoped_definitions_load_context(
    load_type: DefinitionsLoadType = DefinitionsLoadType.INITIALIZATION,
    repository_load_data: Optional[RepositoryLoadData] = None,
) -> Iterator["DefinitionsLoadContext"]:
    context = DefinitionsLoadContext(load_type=load_type, repository_load_data=repository_load_data)
    curr_context = DefinitionsLoadContext.get()
    try:
        DefinitionsLoadContext.set(context)
        yield context
    finally:
        DefinitionsLoadContext.set(curr_context)


@contextmanager
def scoped_reconstruction_serdes_objects(
    state_objects: Optional[Mapping[str, Any]] = None,
) -> Iterator[None]:
    """For test cases that involved state-backed definition objects. This context manager
    allows one to set backing state for a definitions object and test reconstruction
    logic. Creates a DefinitionsLoadContext with DefinitionsLoadType.RECONSTRUCTION,
    serializes the passed in objects and wraps them in
    a CodeLocationReconstructionMetadataValue on your behalf.

    Examples:

    .. code-block:: python

        with scoped_reconstruction_serdes_objects(test_key=ExampleDefState(a_string="bar")):
            loader_cached = ExampleStateBackedDefinitionsLoader("test_key")
            defs = loader_cached.build_defs()
            assert len(defs.get_all_asset_specs()) == 1
            assert defs.get_assets_def("bar")
    """
    with scoped_reconstruction_metadata(
        {k: serialize_value(v) for k, v in state_objects.items()} if state_objects else None
    ):
        yield


@contextmanager
def scoped_reconstruction_metadata(
    reconstruction_metadata: Optional[Mapping[str, Any]] = None,
) -> Iterator[None]:
    """For test cases that involved state-backed definition objects. This context manager
    allows one to set backing reconstruciton metaddata for a definitions object
    and test reconstruction logic. Creates a DefinitionsLoadContext with
    DefinitionsLoadType.RECONSTRUCTION. Wraps each passed value in a
    CodeLocationReconstructionMetadataValue.

    Examples:

    .. code-block:: python

        with scoped_reconstruction_metadata({"test_key": "test_value"}):
            loader_cached = ExampleStateBackedDefinitionsLoader("test_key")
            defs = loader_cached.build_defs()
            assert len(defs.get_all_asset_specs()) == 1
            assert defs.get_assets_def("bar")
    """
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


def unwrap_reconstruction_metadata(repo_def: RepositoryDefinition) -> Mapping[str, Any]:
    """Takes the metadata from a Definitions object and unwraps the CodeLocationReconstructionMetadataValue
    metadata values into a dictionary.
    """
    return {
        k: metadata_value.value
        for k, metadata_value in check.not_none(
            repo_def.repository_load_data
        ).reconstruction_metadata.items()
        if isinstance(metadata_value, CodeLocationReconstructionMetadataValue)
    }
