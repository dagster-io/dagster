from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Sequence, Set, Tuple, Union

from dagster import (
    AssetsDefinition,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.base_asset_graph import AssetKeyOrCheckKey
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult


class AssetGraphExecutionNode(ABC):
    specs: Iterable[Union[AssetSpec, AssetCheckSpec]]

    def __init__(
        self,
        specs: Iterable[Union[AssetSpec, AssetCheckSpec]],
        resource_keys: Optional[Set[str]] = None,
        op_name: Optional[str] = None,
    ) -> None:
        self.specs = specs
        self.resource_keys = resource_keys or set()
        self.op_name = op_name

    @property
    def asset_specs(self) -> List[AssetSpec]:
        return [spec for spec in self.specs if isinstance(spec, AssetSpec)]

    @property
    def keys(self) -> List[AssetKeyOrCheckKey]:
        return [spec.key for spec in self.specs]

    @property
    def asset_keys(self) -> List[AssetKey]:
        return [spec.key for spec in self.asset_specs]

    @abstractmethod
    # TODO: generalize to all result types
    def execute(
        self, context: AssetExecutionContext
    ) -> Union[None, Iterable[PipesExecutionResult]]: ...

    def build_assets_def(self) -> AssetsDefinition:
        # how to handle subsetting?
        # todo handle asset checks
        def _implementation(context) -> Union[MaterializeResult, Tuple[PipesExecutionResult, ...]]:
            results = self.execute(context)

            if results is None:
                # super messed up right now
                if len(self.asset_specs) == 1:
                    return MaterializeResult()
                synthesized_results = []
                for spec in self.asset_specs:
                    synthesized_results.append(MaterializeResult(asset_key=spec.key))
                return tuple(synthesized_results)

            return tuple(results)

        @multi_asset(name=self.op_name, specs=self.specs, required_resource_keys=self.resource_keys)  # type: ignore
        # Subverting typehints shenanigans
        def _asset_def(context):  # type: ignore
            return _implementation(context)

        return _asset_def

    @staticmethod
    def to_assets_defs(
        nodes: Sequence["AssetGraphExecutionNode"],
    ) -> List[AssetsDefinition]:
        return [node.build_assets_def() for node in nodes]
