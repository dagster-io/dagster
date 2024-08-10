from itertools import chain
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, cast

from dagster import AssetMaterialization, MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema

from dagster_airbyte.types import AirbyteOutput, AirbyteTableMetadata


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
    output: AirbyteOutput,
    asset_key_prefix: Sequence[str],
    stream_to_asset_map: Optional[Mapping[str, str]] = None,
) -> Iterator[AssetMaterialization]:
    prefix = output.connection_details.get("prefix") or ""
    # all the streams that are set to be sync'd by this connection
    all_stream_props = {
        prefix + stream["stream"]["name"]: (
            stream.get("stream", {}).get("jsonSchema", {}).get("properties", {})
        )
        for stream in output.connection_details.get("syncCatalog", {}).get("streams", [])
        if stream.get("config", {}).get("selected")
    }

    # stats for each stream that had data sync'd
    all_stream_stats = {
        s["streamName"]: s.get("stats", {})
        for s in _get_attempt(output.job_details.get("attempts", [{}])[-1]).get("streamStats", [])
    }
    stream_to_asset_map = stream_to_asset_map if stream_to_asset_map else {}
    for stream_name, stream_props in all_stream_props.items():
        yield _materialization_for_stream(
            stream_to_asset_map.get(stream_name, stream_name),
            stream_props,
            # if no records are sync'd, no stats will be available for this stream
            all_stream_stats.get(stream_name, {}),
            asset_key_prefix=asset_key_prefix,
        )


def table_to_output_name_fn(table: str) -> str:
    return table.replace("-", "_")


def get_schema_by_table_name(
    stream_table_metadata: Mapping[str, AirbyteTableMetadata],
) -> Mapping[str, TableSchema]:
    schema_by_base_table_name = [(k, v.schema) for k, v in stream_table_metadata.items()]
    schema_by_normalization_table_name = list(
        chain.from_iterable(
            [
                [
                    (k, v.schema)
                    for k, v in cast(
                        Dict[str, AirbyteTableMetadata], meta.normalization_tables
                    ).items()
                ]
                for meta in stream_table_metadata.values()
            ]
        )
    )

    return dict(schema_by_normalization_table_name + schema_by_base_table_name)
