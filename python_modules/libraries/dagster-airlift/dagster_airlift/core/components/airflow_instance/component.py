from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import record
from dagster.components import Component, ComponentLoadContext, Resolvable
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.core.defs_module import (
    DefsFolderComponent,
    find_components_in_current_context,
)
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import (
    AssetPostProcessor,
    ResolvedAssetKey,
    ResolvedAssetSpec,
)
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest, scaffold_with
from pydantic import BaseModel
from typing_extensions import TypeAlias

import dagster_airlift.core as dg_airlift_core
from dagster_airlift.core.airflow_instance import AirflowAuthBackend
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from dagster_airlift.core.load_defs import build_job_based_airflow_defs
from dagster_airlift.core.serialization.serialized_data import DagHandle, TaskHandle
from dagster_airlift.core.utils import asset_object_exists


@dataclass
class ResolvedAirflowBasicAuthBackend(Resolvable):
    type: Literal["basic_auth"]
    webserver_url: str
    username: str
    password: str


@dataclass
class ResolvedAirflowMwaaAuthBackend(Resolvable):
    type: Literal["mwaa"]


@dataclass
class InAirflowAsset(Resolvable):
    spec: ResolvedAssetSpec


@dataclass
class InDagsterAssetRef(Resolvable):
    by_key: ResolvedAssetKey


def resolve_mapped_asset(context: ResolutionContext, model) -> Union[AssetKey, AssetSpec]:
    if isinstance(model, InAirflowAsset.model()):
        return InAirflowAsset.resolve_from_model(context, model).spec
    elif isinstance(model, InDagsterAssetRef.model()):
        return InDagsterAssetRef.resolve_from_model(context, model).by_key
    else:
        raise ValueError(f"Unsupported asset type: {type(model)}")


ResolvedMappedAsset: TypeAlias = Annotated[
    Union[AssetKey, AssetSpec],
    Resolver(
        resolve_mapped_asset,
        model_field_type=Union[InAirflowAsset.model(), InDagsterAssetRef.model()],
    ),
]


@dataclass
class AirflowTaskMapping(Resolvable):
    task_id: str
    assets: Sequence[ResolvedMappedAsset]


@dataclass
class AirflowDagMapping(Resolvable):
    dag_id: str
    assets: Optional[Sequence[ResolvedMappedAsset]] = None
    task_mappings: Optional[Sequence[AirflowTaskMapping]] = None


class AirflowInstanceScaffolderParams(BaseModel):
    name: str
    auth_type: Literal["basic_auth", "mwaa"]


class AirflowInstanceScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return AirflowInstanceScaffolderParams

    def scaffold(self, request: ScaffoldRequest, params: AirflowInstanceScaffolderParams) -> None:
        full_params = {
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
        model_field_type=Union[ResolvedAirflowBasicAuthBackend, ResolvedAirflowMwaaAuthBackend],
    ),
]


@scaffold_with(AirflowInstanceScaffolder)
@dataclass
class AirflowInstanceComponent(Component, Resolvable):
    auth: ResolvedAirflowAuthBackend
    name: str
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None
    mappings: Optional[Sequence[AirflowDagMapping]] = None

    def _get_instance(self) -> dg_airlift_core.AirflowInstance:
        return dg_airlift_core.AirflowInstance(
            auth_backend=self.auth,
            name=self.name,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        # Trying to load itself... but working?
        defs = build_job_based_airflow_defs(
            airflow_instance=self._get_instance(),
            mapped_defs=apply_mappings(defs_in_context(context), self.mappings),
        )
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs


def defs_in_context(context: ComponentLoadContext) -> Definitions:
    return DefsFolderComponent(
        path=context.path,
        children=find_components_in_current_context(context),
        asset_post_processors=None,
    ).build_defs(context)


@record
class MappingCache:
    mappings: Sequence[AirflowDagMapping]
    defs: Definitions

    @property
    def key_to_handle(self) -> Mapping[AssetKey, Union[TaskHandle, DagHandle]]:
        result = {}
        for mapping in self.mappings:
            for task_mapping in mapping.task_mappings:
                for asset in task_mapping.assets:
                    result[
                        asset.by_key if isinstance(asset, InDagsterAssetRef) else asset.spec.key
                    ] = TaskHandle(
                        dag_id=mapping.dag_id,
                        task_id=task_mapping.task_id,
                    )
            for asset in mapping.assets:
                result[asset.spec.key] = DagHandle(
                    dag_id=mapping.dag_id,
                )
        return result


def handle_iterator(
    mappings: Sequence[AirflowDagMapping],
) -> Iterator[
    tuple[Union[TaskHandle, DagHandle], Sequence[Union[InAirflowAsset, InDagsterAssetRef]]]
]:
    for mapping in mappings:
        for task_mapping in mapping.task_mappings:
            yield (
                TaskHandle(dag_id=mapping.dag_id, task_id=task_mapping.task_id),
                task_mapping.assets,
            )
        yield DagHandle(dag_id=mapping.dag_id), mapping.assets


def apply_mappings(defs: Definitions, mappings: Sequence[AirflowDagMapping]) -> Definitions:
    key_to_handle_mapping = {}
    additional_assets = []

    for handle, assets in handle_iterator(mappings):
        if not assets:
            continue
        for asset in assets:
            if isinstance(asset, AssetKey):
                if not asset_object_exists(defs, asset):
                    raise ValueError(f"Asset with key {asset} not found in definitions")
                key_to_handle_mapping[asset] = handle
            elif isinstance(asset, AssetSpec):
                if asset_object_exists(defs, asset.key):
                    raise ValueError(f"Asset with key {asset.key} already exists in definitions")
                additional_assets.append(
                    asset.merge_attributes(metadata={handle.metadata_key: [handle.as_dict]})
                )

    def spec_mapper(spec: AssetSpec) -> AssetSpec:
        if spec.key in key_to_handle_mapping:
            handle = key_to_handle_mapping[spec.key]
            return spec.merge_attributes(metadata={handle.metadata_key: [handle.as_dict]})
        return spec

    return Definitions.merge(
        defs.map_asset_specs(func=spec_mapper), Definitions(assets=additional_assets)
    )
