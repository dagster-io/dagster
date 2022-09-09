from typing import Any, Dict, Iterator, List

from dagster_airbyte.types import AirbyteOutput

from dagster import AssetMaterialization, MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema


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


def _get_attempt(attempt: dict):
    # the attempt field is nested in some API results, and is not in others
    return attempt.get("attempt") or attempt


def generate_materializations(
    output: AirbyteOutput, asset_key_prefix: List[str]
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
