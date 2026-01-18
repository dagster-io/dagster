from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    SourceAsset,
    _check as check,
)
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    CacheableAssetsDefinition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY, KIND_PREFIX

from dagster_airlift.constants import (
    AIRFLOW_SOURCE_METADATA_KEY_PREFIX,
    DAG_ID_TAG_KEY,
    DAG_MAPPING_METADATA_KEY,
    PEERED_DAG_MAPPING_METADATA_KEY,
    TASK_MAPPING_METADATA_KEY,
)

if TYPE_CHECKING:
    from dagster_airlift.core.serialization.serialized_data import DagHandle, TaskHandle


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def airflow_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": ""}


def airlift_mapped_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airliftmapped": ""}


def spec_iterator(
    assets: Optional[
        Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]
    ],
) -> Iterator[AssetSpec]:
    for asset in assets or []:
        if isinstance(asset, AssetsDefinition):
            yield from asset.specs
        elif isinstance(asset, AssetSpec):
            yield asset
        else:
            raise DagsterInvariantViolationError(
                "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs."
            )


def metadata_for_task_mapping(*, task_id: str, dag_id: str) -> dict:
    return {TASK_MAPPING_METADATA_KEY: [{"dag_id": dag_id, "task_id": task_id}]}


def metadata_for_dag_mapping(*, dag_id: str) -> dict:
    return {DAG_MAPPING_METADATA_KEY: [{"dag_id": dag_id}]}


def get_metadata_key(instance_name: str) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{instance_name}"


def is_task_mapped_asset_spec(spec: AssetSpec) -> bool:
    return TASK_MAPPING_METADATA_KEY in spec.metadata


def is_dag_mapped_asset_spec(spec: AssetSpec) -> bool:
    return DAG_MAPPING_METADATA_KEY in spec.metadata


def is_peered_dag_asset_spec(spec: AssetSpec) -> bool:
    return PEERED_DAG_MAPPING_METADATA_KEY in spec.metadata


def task_handles_for_spec(spec: AssetSpec) -> set["TaskHandle"]:
    from dagster_airlift.core.serialization.serialized_data import TaskHandle

    check.param_invariant(is_task_mapped_asset_spec(spec), "spec", "Must be mapped spec")
    task_handles = []
    for task_handle_dict in spec.metadata[TASK_MAPPING_METADATA_KEY]:
        task_handles.append(
            TaskHandle(dag_id=task_handle_dict["dag_id"], task_id=task_handle_dict["task_id"])
        )
    return set(task_handles)


def dag_handles_for_spec(spec: AssetSpec) -> set["DagHandle"]:
    from dagster_airlift.core.serialization.serialized_data import DagHandle

    check.param_invariant(is_dag_mapped_asset_spec(spec), "spec", "Must be mapped spec")
    return {
        DagHandle(dag_id=dag_handle_dict["dag_id"])
        for dag_handle_dict in spec.metadata[DAG_MAPPING_METADATA_KEY]
    }


def peered_dag_handles_for_spec(spec: AssetSpec) -> set["DagHandle"]:
    from dagster_airlift.core.serialization.serialized_data import DagHandle

    check.param_invariant(is_peered_dag_asset_spec(spec), "spec", "Must be mapped spec")
    return {
        DagHandle(dag_id=dag_handle_dict["dag_id"])
        for dag_handle_dict in spec.metadata[PEERED_DAG_MAPPING_METADATA_KEY]
    }


def get_producing_dag_ids(spec: AssetSpec) -> set[str]:
    if is_dag_mapped_asset_spec(spec):
        return {dag_handle.dag_id for dag_handle in dag_handles_for_spec(spec)}
    if is_peered_dag_asset_spec(spec):
        return {dag_handle.dag_id for dag_handle in peered_dag_handles_for_spec(spec)}
    else:
        return {task_handle.dag_id for task_handle in task_handles_for_spec(spec)}


MappedAsset = Union[AssetSpec, AssetsDefinition]


def _type_check_asset(asset: Any) -> MappedAsset:
    return check.inst(
        asset,
        (AssetSpec, AssetsDefinition),
        "Expected passed assets to all be AssetsDefinitions or AssetSpecs.",
    )


def type_narrow_defs_assets(defs: Definitions) -> Sequence[MappedAsset]:
    return [_type_check_asset(asset) for asset in defs.assets or []]


def is_airflow_mapped_job(job: JobDefinition) -> bool:
    return job.tags.get(EXTERNAL_JOB_SOURCE_TAG_KEY) == "airflow"


def dag_handle_from_job(job: JobDefinition) -> "DagHandle":
    from dagster_airlift.core.serialization.serialized_data import DagHandle

    check.invariant(
        is_airflow_mapped_job(job),
        "Job is not an Airflow mapped job. Cannot get dag_id.",
    )
    return DagHandle(dag_id=job.tags[DAG_ID_TAG_KEY])


def airflow_job_tags(dag_id: str) -> Mapping[str, str]:
    return {
        **airflow_kind_dict(),
        EXTERNAL_JOB_SOURCE_TAG_KEY: "airflow",
        DAG_ID_TAG_KEY: dag_id,
    }


def monitoring_job_name(instance_name: str) -> str:
    return f"{instance_name}__airflow_monitoring_job"
