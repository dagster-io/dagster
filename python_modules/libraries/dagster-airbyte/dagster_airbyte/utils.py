from typing import Any, Iterator, Mapping, Sequence

from dagster import AssetMaterialization, MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema

from dagster_airbyte.types import AirbyteOutput


def generate_table_schema(stream_schema_props: Mapping[str, Any]) -> TableSchema:
    return TableSchema(
        columns=sorted(
            [
                TableColumn(name=name, type=str(info.get("type", "unknown")))
                for name, info in stream_schema_props.items()
            ],
            key=lambda col: col.name,
        )
    )


def is_basic_normalization_operation(operation_def: Mapping[str, Any]) -> bool:
    return (
        operation_def.get("operatorType", operation_def.get("operator_type")) == "normalization"
        and operation_def.get("normalization", {}).get("option") == "basic"
    )


def _materialization_for_stream(
    name: str,
    stream_schema_props: Mapping[str, Any],
    stream_stats: Mapping[str, Any],
    asset_key_prefix: Sequence[str],
) -> AssetMaterialization:
    return AssetMaterialization(
        asset_key=[*asset_key_prefix, name],
        metadata={
            "schema": MetadataValue.table_schema(generate_table_schema(stream_schema_props)),
            **{k: v for k, v in stream_stats.items() if v is not None},
        },
    )


def _get_attempt(attempt: dict):
    # the attempt field is nested in some API results, and is not in others
    return attempt.get("attempt") or attempt


def generate_materializations(
    output: AirbyteOutput, asset_key_prefix: Sequence[str]
) -> Iterator[AssetMaterialization]:
    prefix = output.connection_details.get("prefix") or ""
    # all the streams that are set to be sync'd by this connection
    all_stream_props = {
        prefix
        + stream["stream"]["name"]: stream.get("stream", {})
        .get("jsonSchema", {})
        .get("properties", {})
        for stream in output.connection_details.get("syncCatalog", {}).get("streams", [])
        if stream.get("config", {}).get("selected")
    }

    # stats for each stream that had data sync'd
    all_stream_stats = {
        s["streamName"]: s.get("stats", {})
        for s in _get_attempt(output.job_details.get("attempts", [{}])[-1]).get("streamStats", [])
    }
    for stream_name, stream_props in all_stream_props.items():
        yield _materialization_for_stream(
            stream_name,
            stream_props,
            # if no records are sync'd, no stats will be avaiable for this stream
            all_stream_stats.get(stream_name, {}),
            asset_key_prefix=asset_key_prefix,
        )
