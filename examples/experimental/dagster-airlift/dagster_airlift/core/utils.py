from typing import TYPE_CHECKING, Iterable, Iterator, Optional, Set, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    SourceAsset,
    _check as check,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.tags import KIND_PREFIX

from dagster_airlift.constants import (
    AIRFLOW_SOURCE_METADATA_KEY_PREFIX,
    DAG_MAPPING_METADATA_KEY,
    TASK_MAPPING_METADATA_KEY,
)

if TYPE_CHECKING:
    from dagster_airlift.core.serialization.serialized_data import AirflowEntityHandle


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def airflow_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": ""}


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


def get_metadata_key(instance_name: str) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{instance_name}"


def is_mapped_asset_spec(spec: AssetSpec) -> bool:
    return TASK_MAPPING_METADATA_KEY in spec.metadata or DAG_MAPPING_METADATA_KEY in spec.metadata


def is_not_doubly_mapped(spec: AssetSpec) -> bool:
    return not (
        TASK_MAPPING_METADATA_KEY in spec.metadata and DAG_MAPPING_METADATA_KEY in spec.metadata
    )


def airflow_handles_for_spec(spec: AssetSpec) -> Set["AirflowEntityHandle"]:
    from dagster_airlift.core.serialization.serialized_data import DagHandle, TaskHandle

    check.param_invariant(is_mapped_asset_spec(spec), "spec", "Must be mappped spec")
    check.param_invariant(
        is_not_doubly_mapped(spec),
        "spec",
        "AssetSpec cannot have both task and dag mappings. An asset should map either to dags or tasks, but not to both.",
    )
    if TASK_MAPPING_METADATA_KEY in spec.metadata:
        return {TaskHandle(**handle) for handle in spec.metadata[TASK_MAPPING_METADATA_KEY]}
    return {DagHandle(dag_id=dag_id) for dag_id in spec.metadata[DAG_MAPPING_METADATA_KEY]}
