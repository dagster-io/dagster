from typing import AbstractSet, Any, Dict, List, Mapping, Optional, Set

from dagster import (
    AssetKey,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    UrlMetadataValue,
    external_asset_from_spec,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes

from dagster_airlift.core.dag_asset import dag_asset_metadata, dag_description
from dagster_airlift.core.serialization.serialized_data import (
    MappedAirflowTaskData,
    SerializedAirflowDefinitionsData,
)
from dagster_airlift.core.utils import airflow_kind_dict


def tags_for_mapped_tasks(tasks: List[MappedAirflowTaskData]) -> Mapping[str, str]:
    all_not_migrated = all(not task.migrated for task in tasks)
    # Only show the airflow kind if the asset is orchestrated exlusively by airflow
    return airflow_kind_dict() if all_not_migrated else {}


def metadata_for_mapped_tasks(tasks: List[MappedAirflowTaskData]) -> Mapping[str, Any]:
    mapped_task = tasks[0]
    task_info, migration_state = mapped_task.task_info, mapped_task.migrated
    task_level_metadata = {
        "Task Info (raw)": JsonMetadataValue(task_info.metadata),
        "Dag ID": task_info.dag_id,
        "Link to DAG": UrlMetadataValue(task_info.dag_url),
    }
    task_level_metadata[
        "Computed in Task ID" if not migration_state else "Triggered by Task ID"
    ] = task_info.task_id
    return task_level_metadata


def enrich_spec_with_airflow_metadata(
    spec: AssetSpec, tasks: List[MappedAirflowTaskData]
) -> AssetSpec:
    return spec._replace(
        tags={**spec.tags, **tags_for_mapped_tasks(tasks)},
        metadata={**spec.metadata, **metadata_for_mapped_tasks(tasks)},
    )


def make_dag_external_asset(dag_data) -> AssetsDefinition:
    return external_asset_from_spec(
        AssetSpec(
            key=dag_data.dag_info.dag_asset_key,
            description=dag_description(dag_data.dag_info),
            metadata=dag_asset_metadata(dag_data.dag_info, dag_data.source_code),
            tags=airflow_kind_dict(),
            deps=dag_data.leaf_asset_keys,
        )
    )


def key_for_task_asset(dag_id, task_id) -> AssetKey:
    return AssetKey(["airflow_instance", "dag", dag_id, "task", task_id])


@whitelist_for_serdes
@record
class AirflowDefinitionsData:
    instance_name: str
    serialized_data: SerializedAirflowDefinitionsData

    def map_airflow_data_to_spec(self, spec: AssetSpec) -> AssetSpec:
        """If there is airflow data applicable to the asset key, transform the spec and apply the data."""
        mapped_tasks = self.serialized_data.all_mapped_tasks.get(spec.key)
        return enrich_spec_with_airflow_metadata(spec, mapped_tasks) if mapped_tasks else spec

    def construct_dag_assets_defs(self) -> Definitions:
        return Definitions(
            [
                make_dag_external_asset(dag_data)
                for dag_data in self.serialized_data.dag_datas.values()
            ]
        )

    def construct_automapped_dag_assets_def(self) -> Definitions:
        specs = []
        for dag_data in self.serialized_data.dag_datas.values():
            upstream_deps: Dict[str, Set[str]] = {task_id: set() for task_id in dag_data.task_infos}
            for task_id, task_info in dag_data.task_infos.items():
                for downstream_id in task_info.downstream_task_ids:
                    upstream_deps[downstream_id].add(task_id)

            specs.extend(
                AssetSpec(
                    key=key_for_task_asset(dag_data.dag_id, task_id),
                    deps=[
                        key_for_task_asset(dag_data.dag_id, upstream_task_id)
                        for upstream_task_id in upstream_task_ids
                    ],
                )
                for task_id, upstream_task_ids in upstream_deps.items()
            )

        return Definitions.merge(Definitions(assets=specs), self.construct_dag_assets_defs())

    @property
    def all_dag_ids(self) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas.keys())

    def asset_key_for_dag(self, dag_id: str) -> AssetKey:
        return self.serialized_data.dag_datas[dag_id].dag_info.dag_asset_key

    def task_ids_in_dag(self, dag_id: str) -> AbstractSet[str]:
        return set(self.serialized_data.dag_datas[dag_id].task_handle_data.keys())

    def migration_state_for_task(self, dag_id: str, task_id: str) -> Optional[bool]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].migration_state

    def asset_keys_in_task(self, dag_id: str, task_id: str) -> AbstractSet[AssetKey]:
        return self.serialized_data.dag_datas[dag_id].task_handle_data[task_id].asset_keys_in_task
