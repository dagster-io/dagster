import itertools
from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import Annotated, Callable, Literal, Optional, Union, cast

import dagster as dg
import dagster_airlift.core as dg_airlift_core
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core.airflow_instance import AirflowAuthBackend
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from dagster_dbt.asset_utils import get_asset_key_for_model as get_asset_key_for_model
from pydantic import Field

from dagster_components import AssetPostProcessorModel, Component, ComponentLoadContext
from dagster_components.components.airflow_instance.scaffolder import (
    AirflowInstanceComponentScaffolder,
)
from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    ResolvedAssetSpec,
)
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver
from dagster_components.scaffold import scaffold_with


class AirflowBasicAuthBackendModel(ResolvableModel):
    type: Literal["basic_auth"]
    webserver_url: str = Field(default=..., description="The URL of the Airflow webserver.")
    username: str = Field(default=..., description="The username to use for basic authentication.")
    password: str = Field(default=..., description="The password to use for basic authentication.")


class AirflowMwaaAuthBackendModel(ResolvableModel):
    type: Literal["mwaa"]


class AirflowDagSelectionModel(ResolvableModel, ResolvedFrom["AirflowDagSelectionModel"]):
    dag_ids: Optional[list[str]] = Field(
        default=None, description="A subselection of DAG ids to load from the Airflow instance."
    )


class AirflowTaskModel(ResolvableModel):
    task_id: str = Field(default=..., description="The ID of the task.")
    asset_specs: Optional[Sequence[AssetAttributesModel]] = Field(
        default=None, description="Asset specs to optionally associate with this task."
    )


@dataclass
class ResolvedAirflowTask(ResolvedFrom[AirflowTaskModel]):
    task_id: str
    asset_specs: Optional[Sequence[ResolvedAssetSpec]]


class AirflowDagModel(ResolvableModel):
    dag_id: str = Field(default=..., description="The ID of the DAG.")
    asset_specs: Optional[Sequence[AssetAttributesModel]] = Field(
        default=None, description="Asset specs to optionally associate with this DAG."
    )
    task_mappings: Optional[Sequence[AirflowTaskModel]] = Field(
        default=None,
        description="Asset specs to optionally associate with each task within the DAG.",
    )
    make_executable: bool = Field(
        default=True,
        description=(
            "Whether to make the DAG executable in Dagster. "
            "This makes all affiliated Dagster assets executable, with the backing computation kicking off a run of the DAG in Airflow."
        ),
    )


@dataclass
class ResolvedAirflowDag(ResolvedFrom[AirflowDagModel]):
    dag_id: str
    asset_specs: Optional[Sequence[ResolvedAssetSpec]]
    task_mappings: Annotated[Optional[Sequence[ResolvedAirflowTask]], Resolver.from_annotation()]
    make_executable: bool


class AirflowInstanceModel(ResolvableModel):
    auth: Union[AirflowBasicAuthBackendModel, AirflowMwaaAuthBackendModel] = Field(
        default=..., description="The authentication backend to use for the Airflow instance."
    )
    name: str = Field(default=..., description="A unique name for the Airflow instance.")
    dags_to_load: Optional[AirflowDagSelectionModel] = Field(
        default=None,
        description="A subselection of DAG ids to load from the Airflow instance. Defaults to loading all DAGs.",
    )
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = Field(
        default=None, description="Post-processing attributes to apply to the assets."
    )
    dag_mappings: Optional[Sequence[AirflowDagModel]] = Field(
        default=None,
        description="Asset specs to optionally associate with each DAG or task within the Airflow instance.",
    )


def resolve_auth(context: ResolutionContext, model: AirflowInstanceModel) -> AirflowAuthBackend:
    if model.auth.type == "basic_auth":
        return AirflowBasicAuthBackend(
            webserver_url=model.auth.webserver_url,
            username=model.auth.username,
            password=model.auth.password,
        )
    else:
        raise ValueError(f"Unsupported auth type: {model.auth.type}")


@scaffold_with(AirflowInstanceComponentScaffolder)
@dataclass
class AirflowInstanceComponent(Component, ResolvedFrom[AirflowInstanceModel]):
    """Represent an Airflow instance in Dagster as a set of assets. Automatically polls
    and represents the state of the Airflow DAGs in Dagster.

    Scaffold by running `dagster scaffold component dagster_components.airlift.AirflowInstanceComponent`
    in the Dagster project directory.
    """

    auth: Annotated[AirflowAuthBackend, Resolver.from_model(resolve_auth)]
    name: str
    dags_to_load: Annotated[Optional[AirflowDagSelectionModel], Resolver.from_annotation()]
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]], Resolver.from_annotation()
    ]
    dag_mappings: Annotated[Optional[Sequence[ResolvedAirflowDag]], Resolver.from_annotation()]

    def _get_instance(self) -> dg_airlift_core.AirflowInstance:
        return dg_airlift_core.AirflowInstance(
            auth_backend=self.auth,
            name=self.name,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        dag_selector_fn: Optional[Callable[[dg_airlift_core.DagInfo], bool]] = None
        if self.dags_to_load and self.dags_to_load.dag_ids:
            dag_list = self.dags_to_load.dag_ids

            def _dag_selector_fn(dag: dg_airlift_core.DagInfo) -> bool:
                return dag.dag_id in dag_list

            dag_selector_fn = _dag_selector_fn

        airflow_instance = self._get_instance()

        mapped_assets_and_tasks = list(
            dg_airlift_core.assets_with_dag_mappings(
                {
                    dag.dag_id: cast(Sequence[AssetSpec], dag.asset_specs)
                    for dag in self.dag_mappings or []
                    if dag.asset_specs and not dag.make_executable
                }
            )
        ) + [
            *itertools.chain.from_iterable(
                dg_airlift_core.assets_with_task_mappings(
                    dag_id=dag.dag_id,
                    task_mappings={
                        task_mapping.task_id: cast(Sequence[AssetSpec], task_mapping.asset_specs)
                        for task_mapping in dag.task_mappings or []
                    },
                )
                for dag in self.dag_mappings or []
                if dag.task_mappings and not dag.make_executable
            )
        ]

        mapped_assets = []
        for dag in self.dag_mappings or []:
            specs = [
                *dg_airlift_core.assets_with_dag_mappings(
                    {dag.dag_id: cast(Sequence[AssetSpec], dag.asset_specs)}
                    if dag.asset_specs
                    else {}
                ),
                *dg_airlift_core.assets_with_task_mappings(
                    dag_id=dag.dag_id,
                    task_mappings={
                        task_mapping.task_id: cast(Sequence[AssetSpec], task_mapping.asset_specs)
                        for task_mapping in dag.task_mappings or []
                    },
                ),
            ]
            if dag.make_executable:
                if specs:

                    @dg.multi_asset(specs=specs, name=dag.dag_id)
                    def _run_dag() -> Generator[dg.MaterializeResult, None, None]:
                        run_id = airflow_instance.trigger_dag(dag.dag_id)
                        airflow_instance.wait_for_run_completion(dag.dag_id, run_id)
                        if airflow_instance.get_run_state(dag.dag_id, run_id) == "success":
                            for spec in specs:
                                yield dg.MaterializeResult(asset_key=spec.key)
                        else:
                            raise Exception("Dag run failed.")

                    mapped_assets.append(_run_dag)
            else:
                mapped_assets.extend(specs)

        defs = dg_airlift_core.build_defs_from_airflow_instance(
            airflow_instance=airflow_instance,
            dag_selector_fn=dag_selector_fn,
            defs=Definitions(assets=mapped_assets),
        )

        for post_processor in self.asset_post_processors or []:
            defs = post_processor.fn(defs)
        return defs
