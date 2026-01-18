import os
from pathlib import Path
from typing import Any, Optional

import dagster._check as check
from dagster._core.errors import DagsterInvalidInvocationError
from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel, Field


class DbtScaffoldParams(BaseModel):
    init: bool = Field(default=False)
    project_path: Optional[str] = None
    git_url: Optional[str] = None


class DbtProjectComponentScaffolder(Scaffolder[DbtScaffoldParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[DbtScaffoldParams]:
        return DbtScaffoldParams

    def _init_dbt_project(self) -> None:
        try:
            from dbt.cli.main import dbtRunner
        except ImportError:
            raise DagsterInvalidInvocationError(
                "dbt-core is not installed. Please install dbt to scaffold this component."
            )

        dbtRunner().invoke(["init"])

    def _git_url_params(self, git_url: str, project_path: Optional[str]) -> dict[str, Any]:
        repo_relative_path = {"repo_relative_path": project_path} if project_path else {}
        return {"project": {"repo_url": git_url, **repo_relative_path}}

    def scaffold(self, request: ScaffoldRequest[DbtScaffoldParams]) -> None:
        project_root = request.project_root or Path(os.getcwd())
        check.param_invariant(
            not (request.params.init and (request.params.git_url or request.params.project_path)),
            "init and git_url/project_path cannot be set at the same time.",
        )
        if request.params.init:
            self._init_dbt_project()
            subpaths = [
                path for path in project_root.iterdir() if path.is_dir() and path.name != "logs"
            ]
            check.invariant(len(subpaths) == 1, "Expected exactly one subpath to be created.")
            # this path should be relative to this directory
            params = {"project": subpaths[0].name}
        elif request.params.git_url is not None:
            # project_path is the path to the dbt project within the git repository
            project_path = request.params.project_path
            repo_relative_path = {"repo_relative_path": project_path} if project_path else {}
            params = {"project": {"repo_url": request.params.git_url, **repo_relative_path}}
        elif request.params.project_path is not None:
            # project_path represents a local directory
            project_root_tmpl = "{{ context.project_root }}"
            rel_path = os.path.relpath(request.params.project_path, start=project_root)
            path_str = f"{project_root_tmpl}/{rel_path}"
            params = {"project": path_str}
        else:
            params = {"project": None}
        scaffold_component(request, params)
