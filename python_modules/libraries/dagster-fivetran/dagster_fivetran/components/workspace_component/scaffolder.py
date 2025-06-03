from typing import Optional

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel


class FivetranScaffolderParams(BaseModel):
    account_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class FivetranAccountComponentScaffolder(Scaffolder[FivetranScaffolderParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[FivetranScaffolderParams]:
        return FivetranScaffolderParams

    def scaffold(self, request: ScaffoldRequest[FivetranScaffolderParams]) -> None:
        scaffold_component(
            request,
            {
                "workspace": {
                    "account_id": request.params.account_id,
                    "api_key": request.params.api_key,
                    "api_secret": request.params.api_secret,
                }
            },
        )
