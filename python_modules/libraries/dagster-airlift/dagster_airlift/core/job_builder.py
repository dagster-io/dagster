from collections.abc import Mapping, Sequence

from dagster import JobDefinition
from dagster._core.definitions.asset_spec import AssetSpec

from dagster_airlift.core.dag_asset import dag_asset_metadata
from dagster_airlift.core.serialization.serialized_data import SerializedAirflowDefinitionsData
from dagster_airlift.core.utils import (
    airflow_job_tags,
    convert_to_valid_dagster_name,
    spec_iterator,
)


def construct_dag_jobs(
    serialized_data: SerializedAirflowDefinitionsData,
    mapped_specs: Mapping[str, Sequence[AssetSpec]],
) -> Sequence[JobDefinition]:
    """Constructs a job for each DAG in the serialized data. The job will be used to power runs."""
    return [
        JobDefinition.for_external_job(
            asset_keys=[spec.key for spec in spec_iterator(mapped_specs.get(dag_id, []))],
            name=job_name(dag_data.dag_id),
            metadata=dag_asset_metadata(dag_data.dag_info),
            tags=airflow_job_tags(dag_data.dag_id),
        )
        for dag_id, dag_data in serialized_data.dag_datas.items()
    ]


def job_name(dag_id: str) -> str:
    """Constructs a job name from the DAG ID. The job name is used to power runs."""
    return convert_to_valid_dagster_name(dag_id)
