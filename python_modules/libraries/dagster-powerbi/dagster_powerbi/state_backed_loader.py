from abc import ABC, abstractmethod
from typing import Generic, Sequence, Type, TypeVar

from dagster import (
    AssetsDefinition,
    Definitions,
    _check as check,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType

TState = TypeVar("TState")


def cacheable_assets_def_from_loader(
    loader: "StateBackedDefinitionsLoader[TState]", state_type: Type[TState]
) -> CacheableAssetsDefinition:
    return StateBackedDefinitionsLoaderAdapterCacheableAssetsDefinition(loader, state_type)


class StateBackedDefinitionsLoaderAdapterCacheableAssetsDefinition(
    Generic[TState], CacheableAssetsDefinition
):
    def __init__(self, loader: "StateBackedDefinitionsLoader[TState]", state_type: Type[TState]):
        self._loader = loader
        self._state_type = state_type
        super().__init__(unique_id=self._loader.defs_key)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        state = self._loader.fetch_backing_state()
        return [AssetsDefinitionCacheableData(extra_metadata={self._loader.defs_key: state})]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        state = check.inst(
            check.not_none(data[0].extra_metadata)[self._loader.defs_key], self._state_type
        )
        return self._loader.defs_from_state(state).get_asset_graph().assets_defs


class StateBackedDefinitionsLoader(ABC, Generic[TState]):
    def __init__(self, defs_key: str):
        self.defs_key = defs_key

    @abstractmethod
    def fetch_backing_state(self) -> TState: ...

    @abstractmethod
    def defs_from_state(self, state: TState) -> Definitions: ...

    def build_defs(self, context: DefinitionsLoadContext) -> Definitions:
        state = (
            context.reconstruction_metadata[self.defs_key]
            if context.load_type == DefinitionsLoadType.RECONSTRUCTION
            and self.defs_key in context.reconstruction_metadata
            else self.fetch_backing_state()
        )
        return self.defs_from_state(state).with_reconstruction_metadata({self.defs_key: state})
