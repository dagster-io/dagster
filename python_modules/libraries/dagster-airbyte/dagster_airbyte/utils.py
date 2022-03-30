from typing import Any, Dict, List

from dagster_airbyte.types import AirbyteOutput

from dagster import AssetMaterialization, MetadataValue
from dagster.core.definitions.metadata.table import TableColumn, TableSchema


def _materialization_for_stream(
    name: str,
    stream_schema_props: Dict[str, Any],
    stream_stats: Dict[str, Any],
    asset_key_prefix: List[str],
) -> AssetMaterialization:

    return AssetMaterialization(
        asset_key=asset_key_prefix + [name],
        metadata={
            "schema": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=name, type=str(info.get("type", "unknown")))
                        for name, info in stream_schema_props.items()
                    ]
                )
            ),
            **{k: v for k, v in stream_stats.items() if v is not None},
        },
    )


def generate_materializations(output: AirbyteOutput, asset_key_prefix: List[str]):
    prefix = output.connection_details.get("prefix") or ""
    stream_info = {
        prefix + stream["stream"]["name"]: stream
        for stream in output.connection_details.get("syncCatalog", {}).get("streams", [])
        if stream.get("config", {}).get("selected")
    }

    stream_stats = (
        output.job_details.get("attempts", [{}])[-1].get("attempt", {}).get("streamStats", [])
    )
    for stats in stream_stats:
        name = stats["streamName"]

        stream_schema_props = (
            stream_info.get(name, {}).get("stream", {}).get("jsonSchema", {}).get("properties", {})
        )
        yield _materialization_for_stream(
            name,
            stream_schema_props,
            stats.get("stats", {}),
            asset_key_prefix=asset_key_prefix,
        )
