from typing import Optional

from pydantic import BaseModel

from dagster_components.component_scaffolding import scaffold_component_yaml
from dagster_components.core.component_scaffolder import Scaffolder, ScaffoldRequest


class AirflowScaffoldParams(BaseModel):
    webserver_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class AirflowInstanceComponentScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return AirflowScaffoldParams

    def scaffold(self, request: ScaffoldRequest, params: AirflowScaffoldParams) -> None:
        scaffold_component_yaml(
            request,
            {
                "auth": {
                    "type": "basic_auth",
                    "webserver_url": params.webserver_url,
                    "username": params.username,
                    "password": params.password,
                },
                "name": request.target_path.stem,
            },
        )
