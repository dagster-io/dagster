from pathlib import Path
from typing import Iterable, Type

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.project import (
    PipesAssetManifest,
    PipesScript,
    PipesScriptManifest,
)
from dagster._core.pipes.subprocess import PipesSubprocessClient


class ProjectModalKicktestScriptManifest(PipesScriptManifest):
    @property
    def tags(self) -> dict:
        return {
            "kind": "modal",
        }


class ProjectModalKicktestAssetManifest(PipesAssetManifest): ...


class ProjectModalKicktestScript(PipesScript):
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]:
        return subprocess_client.run(
            context=context,
            command=["modal", "run", self.python_script_path],
        ).get_results()

    @classmethod
    def asset_manifest_class(cls) -> Type:
        return ProjectModalKicktestAssetManifest

    @classmethod
    def script_manifest_class(cls) -> Type:
        return ProjectModalKicktestScriptManifest


defs = Definitions(
    assets=ProjectModalKicktestScript.make_pipes_project_defs(Path.cwd(), Path("defs")),
    resources={"subprocess_client": PipesSubprocessClient()},
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
