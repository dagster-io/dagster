from pathlib import Path
from typing import Iterable, Type

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.project import PipesScript, PipesScriptAssetManifest, PipesScriptManifest
from dagster._core.pipes.subprocess import PipesSubprocessClient


class ProjectFooBarScriptManifest(PipesScriptManifest):
    @property
    def tags(self) -> dict:
        return {**{"kind": "python"}, **super().tags}


class ProjectFooBarAssetManifest(PipesScriptAssetManifest):
    @property
    def tags(self) -> dict:
        return {**{"some_default_tags": "default_value", "compute_kind": "python"}, **super().tags}

    @property
    def metadata(self) -> dict:
        return {**{"a_metadata_key": "a_metadata_value"}, **super().metadata}


class ProjectFooBarScript(PipesScript):
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]:
        return subprocess_client.run(
            context=context,
            command=[self.python_executable_path, self.python_script_path],
        ).get_results()

    @classmethod
    def asset_manifest_class(cls) -> Type:
        return ProjectFooBarAssetManifest

    @classmethod
    def script_manifest_class(cls) -> Type:
        return ProjectFooBarScriptManifest


defs = Definitions(
    assets=ProjectFooBarScript.make_pipes_project_defs(Path.cwd(), Path("defs")),
    resources={"subprocess_client": PipesSubprocessClient()},
)

if __name__ == "__main__":
    # defs.get_implicit_global_asset_job_def().execute_in_process()
