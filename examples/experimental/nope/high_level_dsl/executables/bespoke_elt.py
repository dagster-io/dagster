from typing import Dict, List, Literal, Optional, Type

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._core.definitions.result import MaterializeResult
from dagster._manifest.executable import ManifestBackedExecutable
from dagster._manifest.schema import ExecutableManifest
from pydantic import BaseModel


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTExecutableManifestKindOnly(BaseModel):
    kind: Literal["bespoke_elt"]


class BespokeELTExecutableManifest(BaseModel):
    kind: Literal["bespoke_elt"]
    group_name: Optional[str]
    name: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class BespokeELTExecutable(ManifestBackedExecutable):
    @classmethod
    def create_from_manifest(cls, manifest: BespokeELTExecutableManifest) -> "BespokeELTExecutable":
        return BespokeELTExecutable(
            manifest=manifest,
            specs=[
                AssetSpec(key=asset_key, group_name=manifest.group_name)
                for asset_key in manifest.assets.keys()
            ],
        )

    @classmethod
    def manifest_cls(cls) -> Optional[Type[ExecutableManifest]]:
        return BespokeELTExecutableManifest

    def execute(self, context: AssetGraphExecutionContext) -> AssetGraphExecutionResult:
        context.log.info("Running bespoke ELT")
        for spec in self.specs:
            context.log.info(f"Running {spec.key}")
            assert isinstance(spec, AssetSpec)  # only do assets right now
            yield MaterializeResult(asset_key=spec.key)
