import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.core_models import ResolvedAssetSpec

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


@dataclass
class PipesSubprocessScript(Resolvable):
    path: str
    assets: Sequence[ResolvedAssetSpec]


@dataclass
class PipesSubprocessScriptCollectionComponent(Component, Resolvable):
    """Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient."""

    scripts: Sequence[PipesSubprocessScript]

    @cached_property
    def specs_by_path(self) -> Mapping[str, Sequence[AssetSpec]]:
        return {script.path: script.assets for script in self.scripts}

    @staticmethod
    def introspect_from_path(path: Path) -> "PipesSubprocessScriptCollectionComponent":
        return PipesSubprocessScriptCollectionComponent(
            [
                PipesSubprocessScript(path=str(path), assets=[AssetSpec(path.stem)])
                for path in list(path.rglob("*.py"))
            ]
        )

    def build_defs(self, context: ComponentLoadContext) -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions(
            assets=[
                self._create_asset_def(context.path / path, specs)
                for path, specs in self.specs_by_path.items()
            ],
        )

    def _create_asset_def(self, path: Path, specs: Sequence[AssetSpec]) -> AssetsDefinition:
        from dagster._core.pipes.subprocess import PipesSubprocessClient

        # TODO: allow name paraeterization
        @multi_asset(specs=specs, name=f"script_{path.stem}")
        def _asset(context: AssetExecutionContext):
            cmd = [shutil.which("python"), path]
            return PipesSubprocessClient().run(command=cmd, context=context).get_results()

        return _asset
