import shutil
from pathlib import Path
from typing import Optional

from dagster._utils import pushd
from pydantic import BaseModel

from dagster_components.core.component_scaffolder import ScaffoldRequest
from dagster_components.scaffold import scaffold_component_yaml
from dagster_components.scaffoldable.scaffolder import Scaffolder

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class DefinitionsScaffoldParams(BaseModel):
    definitions_path: Optional[str] = None
    object_type: Optional[str] = None


class DefinitionsComponentScaffolder(Scaffolder):
    @classmethod
    def get_params(cls):
        return DefinitionsScaffoldParams

    def scaffold(self, request: ScaffoldRequest, params: DefinitionsScaffoldParams) -> None:
        scaffold_params = (
            params if isinstance(params, DefinitionsScaffoldParams) else DefinitionsScaffoldParams()
        )

        with pushd(str(request.target_path)):
            path = Path(
                scaffold_params.definitions_path
                if scaffold_params.definitions_path
                else "definitions.py"
            )
            path.touch(exist_ok=params.object_type is None)
            if params.object_type:
                shutil.copy(_TEMPLATE_DIR / f"{params.object_type}.py", path)

        scaffold_component_yaml(
            request,
            {"definitions_path": scaffold_params.definitions_path}
            if scaffold_params.definitions_path
            else {},
        )
