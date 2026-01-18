from typing import Optional

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel


class AirbyteScaffolderParams(BaseModel):
    workspace_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AirbyteWorkspaceComponentScaffolder(Scaffolder[AirbyteScaffolderParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[AirbyteScaffolderParams]:
        return AirbyteScaffolderParams

    def scaffold(self, request: ScaffoldRequest[AirbyteScaffolderParams]) -> None:
        scaffold_component(
            request,
            {
                "workspace": {
                    "workspace_id": request.params.workspace_id,
                    "client_id": request.params.client_id,
                    "client_secret": request.params.client_secret,
                }
            },
        )
