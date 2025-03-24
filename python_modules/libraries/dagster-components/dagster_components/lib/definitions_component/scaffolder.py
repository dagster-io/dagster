from pathlib import Path
from typing import Optional

from dagster._utils import pushd
from pydantic import BaseModel

from dagster_components.component.component_scaffolder import ScaffoldRequest
from dagster_components.component_scaffolding import scaffold_component_yaml
from dagster_components.scaffold.scaffold import Scaffolder


class DefinitionsScaffoldParams(BaseModel):
    definitions_path: Optional[str] = None


class DefinitionsComponentScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls):
        return DefinitionsScaffoldParams

    def scaffold(self, request: ScaffoldRequest, params: DefinitionsScaffoldParams) -> None:
        scaffold_params = (
            params if isinstance(params, DefinitionsScaffoldParams) else DefinitionsScaffoldParams()
        )

        with pushd(str(request.target_path)):
            Path(
                scaffold_params.definitions_path
                if scaffold_params.definitions_path
                else "definitions.py"
            ).touch(exist_ok=True)

        scaffold_component_yaml(
            request,
            {"definitions_path": scaffold_params.definitions_path}
            if scaffold_params.definitions_path
            else {},
        )
