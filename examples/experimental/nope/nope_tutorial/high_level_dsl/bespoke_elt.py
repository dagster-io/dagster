from typing import Dict, List, Literal, Optional

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutable,
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._core.definitions.result import MaterializeResult
from pydantic import BaseModel


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTExecutableManifest(BaseModel):
    kind: Literal["bespoke_elt"]
    name: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class BespokeELTExecutable(AssetGraphExecutable):
    def __init__(self, group_name: str, manifest: BespokeELTExecutableManifest):
        super().__init__(
            specs=[
                AssetSpec(key=asset_key, group_name=group_name)
                for asset_key in manifest.assets.keys()
            ]
        )

    def execute(self, context: AssetGraphExecutionContext) -> AssetGraphExecutionResult:
        context.log.info("Running bespoke ELT")
        for spec in self.specs:
            context.log.info(f"Running {spec.key}")
            assert isinstance(spec, AssetSpec)  # only do assets right now
            yield MaterializeResult(asset_key=spec.key)
