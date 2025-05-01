from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Optional, Union

from dagster._core.definitions.definitions_class import Definitions
from dagster.components import Component, ComponentLoadContext, Resolvable
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetPostProcessor
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest, scaffold_with
from pydantic import BaseModel
from typing_extensions import TypeAlias

import dagster_airlift.core as dg_airlift_core
from dagster_airlift.core.airflow_instance import AirflowAuthBackend
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from dagster_airlift.core.load_defs import build_job_based_airflow_defs


@dataclass
class AirflowBasicAuthBackendModel(Resolvable):
    type: Literal["basic_auth"]
    webserver_url: str
    username: str
    password: str


@dataclass
class AirflowMwaaAuthBackendModel(Resolvable):
    type: Literal["mwaa"]


class AirflowInstanceScaffolderParams(BaseModel):
    name: str
    auth_type: Literal["basic_auth", "mwaa"]


class AirflowInstanceScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return AirflowInstanceScaffolderParams

    def scaffold(self, request: ScaffoldRequest, params: AirflowInstanceScaffolderParams) -> None:
        full_params: dict[str, Any] = {
            "name": params.name,
        }
        if params.auth_type == "basic_auth":
            full_params["auth"] = {
                "type": "basic_auth",
                "webserver_url": '{{ env("AIRFLOW_WEBSERVER_URL") }}',
                "username": '{{ env("AIRFLOW_USERNAME") }}',
                "password": '{{ env("AIRFLOW_PASSWORD") }}',
            }
        else:
            raise ValueError(f"Unsupported auth type: {params.auth_type}")
        scaffold_component(request, full_params)


def resolve_auth(context: ResolutionContext, model) -> AirflowAuthBackend:
    if model.auth.type == "basic_auth":
        return AirflowBasicAuthBackend(
            webserver_url=model.auth.webserver_url,
            username=model.auth.username,
            password=model.auth.password,
        )
    else:
        raise ValueError(f"Unsupported auth type: {model.auth.type}")


ResolvedAirflowAuthBackend: TypeAlias = Annotated[
    AirflowAuthBackend,
    Resolver.from_model(
        resolve_auth,
        model_field_type=Union[AirflowBasicAuthBackendModel, AirflowMwaaAuthBackendModel],
    ),
]


@scaffold_with(AirflowInstanceScaffolder)
@dataclass
class AirflowInstanceComponent(Component, Resolvable):
    auth: ResolvedAirflowAuthBackend
    name: str
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def _get_instance(self) -> dg_airlift_core.AirflowInstance:
        return dg_airlift_core.AirflowInstance(
            auth_backend=self.auth,
            name=self.name,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = build_job_based_airflow_defs(
            airflow_instance=self._get_instance(),
        )
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs
