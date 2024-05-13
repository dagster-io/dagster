import shutil
from functools import cached_property
from typing import List, Literal, Optional, Type

from pydantic import BaseModel

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.factory.executable import (
    AssetGraphExecutionContext,
    AssetGraphExecutionResult,
)
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._manifest.executable import ManifestBackedExecutable


class SubprocessAssetManifest(BaseModel):
    key: str
    deps: List[str]
    group_name: Optional[str] = None


class SubprocessExecutableManifest(BaseModel):
    kind: Literal["subprocess"]
    python_script_path: str
    assets: List[SubprocessAssetManifest]
    group_name: Optional[str] = None


class PipesSubprocessManifestExecutable(ManifestBackedExecutable):
    @classmethod
    def create_from_manifest(
        cls, manifest: SubprocessExecutableManifest
    ) -> "PipesSubprocessManifestExecutable":
        return PipesSubprocessManifestExecutable(
            manifest=manifest,
            specs=[
                AssetSpec(
                    key=AssetKey.from_user_string(asset_key_string=asset_manifest.key),
                    deps=[AssetKey.from_user_string(dep) for dep in asset_manifest.deps],
                    group_name=asset_manifest.group_name
                    if asset_manifest.group_name
                    else manifest.group_name,
                )
                for asset_manifest in manifest.assets
            ],
        )

    @property
    def python_script_path(self) -> str:
        return self.manifest.python_script_path

    @cached_property
    def python_executable_path(self) -> str:
        python_executable = shutil.which("python")
        if not python_executable:
            raise ValueError("Python executable not found.")
        return python_executable

    def execute(
        self, context: AssetGraphExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> AssetGraphExecutionResult:
        command = [self.python_executable_path, self.python_script_path]
        results = subprocess_client.run(
            context=context.to_op_execution_context(), command=command
        ).get_results()

        context.log.info(f"Subprocess {self.python_script_path} completed with results: {results}")
        return results

    @classmethod
    def manifest_cls(cls) -> Type[BaseModel]:
        return SubprocessExecutableManifest
