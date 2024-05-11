from typing import Literal

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutable,
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._core.definitions.result import MaterializeResult
from pydantic import BaseModel


class DbtExecutableManifest(BaseModel):
    kind: Literal["dbt_manifest"]
    manifest_json_path: str


class DbtManifestExecutable(AssetGraphExecutable):
    def __init__(self, group_name: str, manifest: DbtExecutableManifest):
        super().__init__(
            specs=[AssetSpec(key=asset_key, group_name=group_name) for asset_key in ["hardcoded"]]
        )

    def execute(self, context: AssetGraphExecutionContext) -> AssetGraphExecutionResult:
        context.log.info("Run dbt project")
        return [MaterializeResult(asset_key="hardcoded")]
