import json
from collections.abc import Iterable, Sequence
from typing import Optional, TypeVar, Union, cast

import dagster._check as check
from dagster._core.definitions.metadata.external_metadata import (
    EXTERNAL_METADATA_TYPE_INFER,
    EXTERNAL_METADATA_TYPES,
    EXTERNAL_METADATA_VALUE_KEYS,
    ExternalMetadataValue,
    metadata_map_from_external,
)
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.storage.tags import EXTERNALLY_MANAGED_ASSETS_TAG

from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY, OBSERVATION_RUN_TAG_KEY
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance
from dagster_airlift.core.serialization.serialized_data import DagHandle, TaskHandle


def structured_log(context: OpExecutionContext, message: str) -> None:
    context.log.info(f"[Airflow Monitoring Job]: {message}")


def get_dagster_run_for_airflow_repr(
    context: OpExecutionContext, airflow_repr: Union[DagRun, TaskInstance]
) -> Optional[DagsterRun]:
    return next(
        iter(
            context.instance.get_runs(
                filters=RunsFilter(
                    tags={
                        DAG_RUN_ID_TAG_KEY: airflow_repr.run_id,
                        DAG_ID_TAG_KEY: airflow_repr.dag_id,
                        OBSERVATION_RUN_TAG_KEY: "true",
                    }
                ),
            )
        ),
        None,
    )


def get_externally_managed_runs_from_handle(
    context: OpExecutionContext, handle: Union[DagHandle, TaskHandle], run_id: str
) -> Sequence[DagsterRun]:
    return context.instance.get_runs(
        filters=RunsFilter(
            tags={
                **handle.identifying_tags,
                DAG_RUN_ID_TAG_KEY: run_id,
                EXTERNALLY_MANAGED_ASSETS_TAG: "true",
            },
        )
    )


_T = TypeVar("_T")


def _assert_param_value(value: _T, expected_values: Iterable[_T]) -> _T:
    if value not in expected_values:
        raise Exception(
            f"Invalid value when translating metadata from logs. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def extract_metadata_from_logs(context: OpExecutionContext, logs: str) -> dict[str, MetadataValue]:
    metadata = {}
    import re

    matches = re.findall(r"DAGSTER_START(.*?)DAGSTER_END", logs, re.DOTALL)
    for match in matches:
        try:
            raw_external_metadata_map = json.loads(match)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON found in logs for match: {match}. JSON error: {e}")
        check.mapping_param(raw_external_metadata_map, "raw_external_metadata_map")
        new_external_metadata_map = {}
        for key, value in raw_external_metadata_map.items():
            if not isinstance(key, str):
                raise Exception(
                    f"Invalid type when translating metadata from logs. Expected a dict with string"
                    f" keys, got a key `{key}` of type `{type(key)}`."
                )
            elif isinstance(value, dict):
                if not {*value.keys()} == EXTERNAL_METADATA_VALUE_KEYS:
                    raise Exception(
                        f"Invalid type when translating metadata from logs. Expected a dict with"
                        " string keys and values that are either raw metadata values or dictionaries"
                        f" with schema `{{raw_value: ..., type: ...}}`. Got a value `{value}`."
                    )
                _assert_param_value(value["type"], EXTERNAL_METADATA_TYPES)
                new_external_metadata_map[key] = cast("ExternalMetadataValue", value)
            else:
                new_external_metadata_map[key] = {
                    "raw_value": value,
                    "type": EXTERNAL_METADATA_TYPE_INFER,
                }

        metadata_map = metadata_map_from_external(new_external_metadata_map)
        metadata.update(metadata_map)

    return metadata
