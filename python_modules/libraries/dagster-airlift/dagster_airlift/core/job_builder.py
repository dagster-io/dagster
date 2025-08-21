from collections.abc import Mapping, Sequence

from dagster import JobDefinition
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.decorators.job_decorator import job

from dagster_airlift.core.dag_asset import peered_dag_asset_metadata
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    SerializedDagData,
)
from dagster_airlift.core.utils import airflow_job_tags, convert_to_valid_dagster_name


def construct_dag_jobs(
    serialized_data: SerializedAirflowDefinitionsData,
    mapped_specs: Mapping[str, Sequence[AssetSpec]],
) -> Sequence[JobDefinition]:
    """Constructs a job for each DAG in the serialized data. The job will be used to power runs."""
    return [
        JobDefinition.for_external_job(
            asset_keys=[spec.key for spec in mapped_specs[dag_id]],
            name=job_name(dag_id),
            metadata=peered_dag_asset_metadata(dag_data.dag_info, dag_data.source_code),
            tags=airflow_job_tags(dag_id),
        )
        for dag_id, dag_data in serialized_data.dag_datas.items()
    ]


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
