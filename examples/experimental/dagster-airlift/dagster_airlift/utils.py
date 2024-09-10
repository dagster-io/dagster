from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union

from dagster import (
    AssetSpec,
    JsonMetadataValue,
    _check as check,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._record import record

from dagster_airlift.constants import AIRFLOW_MAPPING_METADATA_KEY


class MappingType(Enum):
    DAG = "dag"
    TASK = "task"


@record
class MapsToDag:
    dag_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": MappingType.DAG.value, "dag_id": self.dag_id}

    @staticmethod
    def from_dict(value: Dict[str, Any]) -> "MapsToDag":
        return MapsToDag(dag_id=value["dag_id"])


@record
class MapsToTask:
    dag_id: str
    task_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": MappingType.TASK.value, "dag_id": self.dag_id, "task_id": self.task_id}

    @staticmethod
    def from_dict(value: Dict[str, Any]) -> "MapsToTask":
        return MapsToTask(dag_id=value["dag_id"], task_id=value["task_id"])


MapsToAirflow = Union[MapsToDag, MapsToTask]


def from_dict(value: Dict[str, Any]) -> MapsToAirflow:
    return (
        MapsToDag.from_dict(value)
        if value["type"] == MappingType.DAG.value
        else MapsToTask.from_dict(value)
    )


def mappings_from_asset(asset: Union[AssetSpec, AssetsDefinition]) -> Optional[List[MapsToAirflow]]:
    """Extract mappings from the metadata of an asset spec."""
    spec = asset if isinstance(asset, AssetSpec) else next(iter(asset.specs))
    if AIRFLOW_MAPPING_METADATA_KEY not in spec.metadata:
        return None
    metadata_list = check.list_param(
        check.inst(
            spec.metadata[AIRFLOW_MAPPING_METADATA_KEY],
            JsonMetadataValue,
            "Expected airflow mapping to be a JsonMetadataValue",
        ).value,
        "expected airflow mapping to be a list",
        of_type=dict,
    )

    return [from_dict(mapping) for mapping in metadata_list]


def task_mappings_from_asset(asset: Union[AssetSpec, AssetsDefinition]) -> List[MapsToTask]:
    return check.list_param(mappings_from_asset(asset), "mappings", of_type=MapsToTask)


def dag_mappings_from_asset(asset: Union[AssetSpec, AssetsDefinition]) -> List[MapsToDag]:
    return check.list_param(mappings_from_asset(asset), "mappings", of_type=MapsToDag)


def map_to_task(*, spec: AssetSpec, dag_id: str, task_id: str) -> AssetSpec:
    """Add a mapping from the asset to a task in an Airflow DAG. Respects existing mappings."""
    return _extract_metadata_and_add_mapping(
        spec=spec, mapping=MapsToTask(dag_id=dag_id, task_id=task_id)
    )


def map_to_dag(*, spec: AssetSpec, dag_id: str) -> AssetSpec:
    """Add a mapping from the asset to a DAG in Airflow. Respects existing mappings."""
    return _extract_metadata_and_add_mapping(spec=spec, mapping=MapsToDag(dag_id=dag_id))


def _extract_metadata_and_add_mapping(*, spec: AssetSpec, mapping: MapsToAirflow) -> AssetSpec:
    """Add a mapping to the asset. Respects existing mappings."""
    new_mappings = (mappings_from_asset(spec) or []) + [mapping]
    check.invariant(
        all(isinstance(mapping, MapsToDag) for mapping in new_mappings)
        or all(isinstance(mapping, MapsToTask) for mapping in new_mappings),
        "All mappings must be of the same type",
    )
    return spec_with_metadata(
        spec,
        {
            AIRFLOW_MAPPING_METADATA_KEY: JsonMetadataValue(
                [mapping.to_dict() for mapping in (mappings_from_asset(spec) or []) + [mapping]]
            )
        },
    )


def spec_with_metadata(spec: AssetSpec, metadata: Mapping[str, Any]) -> "AssetSpec":
    return spec._replace(metadata={**spec.metadata, **metadata})


def maps_to_dag_metadata(dag_id: str) -> Mapping[str, Any]:
    return {AIRFLOW_MAPPING_METADATA_KEY: JsonMetadataValue([MapsToDag(dag_id=dag_id).to_dict()])}


def maps_to_task_metadata(dag_id: str, task_id: str) -> Mapping[str, Any]:
    return {
        AIRFLOW_MAPPING_METADATA_KEY: JsonMetadataValue(
            [MapsToTask(dag_id=dag_id, task_id=task_id).to_dict()]
        )
    }


def is_task_mapped(asset: Union[AssetSpec, AssetsDefinition]) -> bool:
    mappings = mappings_from_asset(asset)
    return isinstance(next(iter(mappings)), MapsToTask) if mappings else False
