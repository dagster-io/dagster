from typing import Optional

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest
from pydantic import BaseModel


class CensusScaffolderParams(BaseModel):
    api_key: Optional[str] = None


class CensusComponentScaffolder(Scaffolder[CensusScaffolderParams]):
    @classmethod
    def get_scaffold_params(cls) -> type[CensusScaffolderParams]:
        return CensusScaffolderParams

    def scaffold(self, request: ScaffoldRequest[CensusScaffolderParams]) -> None:
        scaffold_component(
            request,
            {
                "workspace": {
                    "api_key": "{{ env.CENSUS_API_KEY }}",
                }
            },
        )
