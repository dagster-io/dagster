import os
from pathlib import Path
from typing import Optional

import dagster._check as check
from dagster.components.component.component_scaffolder import Scaffolder, ScaffoldRequest
from dagster.components.component_scaffolding import scaffold_component
from dbt.cli.main import dbtRunner
from pydantic import BaseModel, Field


class DbtScaffoldParams(BaseModel):
    init: bool = Field(default=False)
    project_path: Optional[str] = None


class DbtProjectComponentScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return DbtScaffoldParams

    def scaffold(self, request: ScaffoldRequest, params: DbtScaffoldParams) -> None:
        cwd = os.getcwd()
        if params.project_path:
            path_str = f"{'{{ project_root }}'}/{os.path.relpath(params.project_path, start=cwd)}"

        elif params.init:
            dbtRunner().invoke(["init"])
            subpaths = [
                path for path in Path(cwd).iterdir() if path.is_dir() and path.name != "logs"
            ]
            check.invariant(len(subpaths) == 1, "Expected exactly one subpath to be created.")
            # this path should be relative to this directory
            path_str = subpaths[0].name
        else:
            path_str = None

        scaffold_component(request, {"project": path_str})
