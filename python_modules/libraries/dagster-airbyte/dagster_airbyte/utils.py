from typing import Any, Dict, List

from dagster_airbyte.types import AirbyteOutput

from dagster import AssetMaterialization, MetadataValue
from dagster.core.definitions.metadata.table import TableColumn, TableSchema


def _materialization_for_stream(
    name: str,
    stream_info: Dict[str, Any],
    stream_stats: Dict[str, Any],
    asset_key_prefix: List[str],
) -> AssetMaterialization:

    return AssetMaterialization(
        asset_key=asset_key_prefix + [name],
        metadata={
            "schema": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=name, type=str(info["type"]))
                        for name, info in stream_info["stream"]["jsonSchema"]["properties"].items()
                    ]
                )
            ),
            "columns": ",".join(
                name for name in stream_info["stream"]["jsonSchema"]["properties"].keys()
            ),
            **{k: v for k, v in stream_stats.items() if v is not None},
        },
    )


def generate_materializations(output: AirbyteOutput, asset_key_prefix: List[str]):
    prefix = output.connection_details.get("prefix", "")
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
        yield _materialization_for_stream(
            name,
            stream_info[name],
            stats.get("stats", {}),
            asset_key_prefix=asset_key_prefix,
        )
