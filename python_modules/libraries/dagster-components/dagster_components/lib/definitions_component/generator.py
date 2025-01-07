from pathlib import Path
from typing import Optional

from dagster._utils import pushd
from pydantic import BaseModel

from dagster_components.core.component import ComponentGenerator
from dagster_components.core.component_generator import ComponentGenerateRequest
from dagster_components.generate import generate_component_yaml


class DefinitionsGenerateParams(BaseModel):
    definitions_path: Optional[str] = None


class DefinitionsComponentGenerator(ComponentGenerator):
    @classmethod
    def get_params_schema_type(cls):
        return DefinitionsGenerateParams

    def generate_files(
        self, request: ComponentGenerateRequest, params: DefinitionsGenerateParams
    ) -> None:
        generate_params = (
            params if isinstance(params, DefinitionsGenerateParams) else DefinitionsGenerateParams()
        )

        with pushd(str(request.component_instance_root_path)):
            Path(
                generate_params.definitions_path
                if generate_params.definitions_path
                else "definitions.py"
            ).touch(exist_ok=True)

        generate_component_yaml(
            request,
            {"definitions_path": generate_params.definitions_path}
            if generate_params.definitions_path
            else {},
        )
