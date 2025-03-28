from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from dagster import AssetExecutionContext, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster_components import Component, ComponentLoadContext
from dagster_shared.record import record


@record
class OpSpec:
    name: str


@record
class AssetsDefinitionsArgs:
    op: OpSpec
    specs: list[AssetSpec]
    deps: list[CoercibleToAssetDep]


@dataclass
class AssetsDefinitionComponent(Component, ABC):
    op_spec: OpSpec
    specs: list[AssetSpec]
    resources: Optional[dict[str, object]] = None

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        @multi_asset(name=self.op_spec.name, specs=self.specs)
        def _the_asset(context: AssetExecutionContext):
            return self.execute(context)

        return Definitions(assets=[_the_asset], resources=self.resources)

    @abstractmethod
    def execute(self, context: AssetExecutionContext): ...


class CompositeComponent(Component):
    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        return Definitions.merge(
            *[
                component.build_defs(load_context)
                for component in self.build_components(load_context)
            ]
        )

    @abstractmethod
    def build_components(self, load_context: ComponentLoadContext) -> Iterable[Component]: ...
