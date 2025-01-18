from pathlib import Path
from typing import Optional

from dagster._utils import pushd
from pydantic import BaseModel

from dagster_components.core.component import ComponentScaffolder
from dagster_components.core.component_scaffolder import ComponentScaffoldRequest
from dagster_components.scaffold import scaffold_component_yaml


class DefinitionsScaffoldParams(BaseModel):
    definitions_path: Optional[str] = None


class DefinitionsComponentScaffolder(ComponentScaffolder):
    @classmethod
    def get_params_schema_type(cls):
        return DefinitionsScaffoldParams

    def scaffold(
        self, request: ComponentScaffoldRequest, params: DefinitionsScaffoldParams
    ) -> None:
        scaffold_params = (
            params if isinstance(params, DefinitionsScaffoldParams) else DefinitionsScaffoldParams()
        )

        with pushd(str(request.component_instance_root_path)):
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
