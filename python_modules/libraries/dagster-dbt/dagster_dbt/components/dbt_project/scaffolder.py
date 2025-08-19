import os
from pathlib import Path
from typing import Optional

import dagster._check as check
from dagster._core.errors import DagsterInvalidInvocationError
from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel, Field


class DbtScaffoldParams(BaseModel):
    init: bool = Field(default=False)
    project_path: Optional[str] = None


class DbtProjectComponentScaffolder(Scaffolder[DbtScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DbtScaffoldParams]:
        return DbtScaffoldParams

    def scaffold(self, request: ScaffoldRequest[DbtScaffoldParams]) -> None:
        project_root = request.project_root or os.getcwd()
        if request.params.project_path:
            project_root_tmpl = "{{ project_root }}"
            rel_path = os.path.relpath(request.params.project_path, start=project_root)
            path_str = f"{project_root_tmpl}/{rel_path}"

        elif request.params.init:
            try:
                from dbt.cli.main import dbtRunner
            except ImportError:
                raise DagsterInvalidInvocationError(
                    "dbt-core is not installed. Please install dbt to scaffold this component."
                )

            dbtRunner().invoke(["init"])
            subpaths = [
                path
                for path in Path(project_root).iterdir()
                if path.is_dir() and path.name != "logs"
            ]
            check.invariant(len(subpaths) == 1, "Expected exactly one subpath to be created.")
            # this path should be relative to this directory
            path_str = subpaths[0].name
        else:
            path_str = None

        scaffold_component(request, {"project": path_str})
