from collections.abc import Mapping, Sequence
from typing import Union

from dagster import JobDefinition
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
    define_asset_job,
)

from dagster_airlift.core.dag_asset import dag_asset_metadata
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    SerializedDagData,
)
from dagster_airlift.core.utils import airflow_job_tags, convert_to_valid_dagster_name


def construct_dag_jobs(
    serialized_data: SerializedAirflowDefinitionsData,
    mapped_assets: Mapping[str, Sequence[Union[AssetSpec, AssetsDefinition]]],
) -> Sequence[Union[UnresolvedAssetJobDefinition, JobDefinition]]:
    """Constructs a job for each DAG in the serialized data. The job will be used to power runs."""
    jobs = []
    for dag_id, dag_data in serialized_data.dag_datas.items():
        assets_produced_by_dag = mapped_assets.get(dag_id)
        if assets_produced_by_dag:
            jobs.append(dag_asset_job(dag_data, assets_produced_by_dag))
        else:
            jobs.append(dag_non_asset_job(dag_data))
    return jobs


def dag_asset_job(
    dag_data: SerializedDagData, assets: Sequence[Union[AssetsDefinition, AssetSpec]]
) -> UnresolvedAssetJobDefinition:
    specs: list[AssetSpec] = []
    for asset in assets:
        if not isinstance(asset, AssetSpec):
            raise Exception(
                "Fully resolved assets definition passed to dag job creation not yet supported."
            )
        specs.append(asset)
    # Eventually we'll have to handle fully resolved AssetsDefinition objects here but it's a whole
    # can of worms. For now, we enforce that only assetSpec objects are passed in.
    return define_asset_job(
        name=job_name(dag_data.dag_id),
        metadata=dag_asset_metadata(dag_data.dag_info),
        tags=airflow_job_tags(dag_data.dag_id),
        selection=[asset.key for asset in specs],
    )


def job_name(dag_id: str) -> str:
    """Constructs a job name from the DAG ID. The job name is used to power runs."""
    return convert_to_valid_dagster_name(dag_id)


def dag_non_asset_job(dag_data: SerializedDagData) -> JobDefinition:
    @job(
        name=convert_to_valid_dagster_name(dag_data.dag_id),
        tags=airflow_job_tags(dag_data.dag_id),
    )
    def dummy_job():
        pass

    return dummy_job
