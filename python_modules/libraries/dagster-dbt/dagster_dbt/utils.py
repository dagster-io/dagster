from typing import Any, Dict, Iterator, List, Optional

import dateutil
from dagster import AssetMaterialization, EventMetadataEntry, check

from .types import DbtOutput


def _get_asset_materialization(
    unique_id: str, asset_key_prefix: List[str], metadata: List[EventMetadataEntry]
) -> AssetMaterialization:
    return AssetMaterialization(
        description=f"dbt node: {unique_id}",
        metadata_entries=metadata,
        asset_key=asset_key_prefix + unique_id.split("."),
    )


def _node_result_to_metadata(node_result: Dict[str, Any]) -> List[EventMetadataEntry]:
    return [
        EventMetadataEntry.text(
            text=node_result["config"]["materialized"],
            label="Materialization Strategy",
        ),
        EventMetadataEntry.text(text=node_result["database"], label="Database"),
        EventMetadataEntry.text(text=node_result["schema"], label="Schema"),
        EventMetadataEntry.text(text=node_result["alias"], label="Alias"),
        EventMetadataEntry.text(text=node_result["description"], label="Description"),
    ]


def _timing_to_metadata(timings: List[Dict[str, Any]]) -> List[EventMetadataEntry]:
    metadata = []
    for timing in timings:
        if timing["name"] == "execute":
            desc = "Execution"
        elif timing["name"] == "compile":
            desc = "Compilation"
        else:
            continue

        started_at = dateutil.parser.isoparse(timing["started_at"])
        completed_at = dateutil.parser.isoparse(timing["completed_at"])
        duration = completed_at - started_at
        metadata.extend(
            [
                EventMetadataEntry.text(
                    text=started_at.isoformat(timespec="seconds"), label=f"{desc} Started At"
                ),
                EventMetadataEntry.text(
                    text=started_at.isoformat(timespec="seconds"), label=f"{desc} Completed At"
                ),
                EventMetadataEntry.float(value=duration.total_seconds(), label=f"{desc} Duration"),
            ]
        )
    return metadata


def result_to_materialization(
    result: Dict[str, Any], asset_key_prefix: List[str] = None, docs_url: str = None
) -> Optional[AssetMaterialization]:
    """
    This is a hacky solution that attempts to consolidate parsing many of the potential formats
    that dbt can provide its results in. This is known to work for CLI Outputs for dbt versions 0.18+,
    as well as RPC responses for a similar time period, but as the RPC response schema is not documented
    nor enforced, this can become out of date easily.
    """

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # status comes from set of fields rather than "status"
    if "fail" in result:
        success = not result.get("fail") and not result.get("skip") and not result.get("error")
    else:
        success = result["status"] == "success"

    if not success:
        return None

    # all versions represent timing the same way
    metadata = [
        EventMetadataEntry.float(value=result["execution_time"], label="Execution Time (seconds)")
    ] + _timing_to_metadata(result["timing"])

    # working with a response that contains the node block (RPC and CLI 0.18.x)
    if "node" in result:

        unique_id = result["node"]["unique_id"]
        metadata += _node_result_to_metadata(result["node"])
    else:
        unique_id = result["unique_id"]

    id_prefix = unique_id.split(".")

    # only generate materializations for models
    if id_prefix[0] != "model":
        return None

    if docs_url:
        metadata = [
            EventMetadataEntry.url(url=f"{docs_url}#!/model/{unique_id}", label="docs_url")
        ] + metadata

    return AssetMaterialization(
        description=f"dbt node: {unique_id}",
        metadata_entries=metadata,
        asset_key=asset_key_prefix + id_prefix,
    )


def generate_materializations(
    dbt_output: DbtOutput, asset_key_prefix: Optional[List[str]] = None
) -> Iterator[AssetMaterialization]:

    """
    This function yields :py:class:`dagster.AssetMaterialization` events for each model created by
    a dbt run command (with information parsed from a :py:class:`~DbtOutput` object).

    Note that this will not work with output from the `dbt_rpc_resource`, because this resource does
    not wait for a response from the RPC server before returning. Instead, use the
    `dbt_rpc_sync_resource`, which will wait for execution to complete.

    Examples:

    .. code-block:: python

        from dagster import op, Output
        from dagster_dbt.utils import generate_materializations
        from dagster_dbt import dbt_cli_resource, dbt_rpc_sync_resource

        @op(required_resource_keys={"dbt"})
        def my_custom_dbt_run(context):
            dbt_output = context.resources.dbt.run()
            for materialization in generate_materializations(dbt_output):
                # you can modify the materialization object to add extra metadata, if desired
                yield materialization
            yield Output(my_dbt_output)

        @job(resource_defs={{"dbt":dbt_cli_resource}})
        def my_dbt_cli_job():
            my_custom_dbt_run()

        @job(resource_defs={{"dbt":dbt_rpc_sync_resource}})
        def my_dbt_rpc_job():
            my_custom_dbt_run()
    """

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    for result in dbt_output.result["results"]:
        materialization = result_to_materialization(
            result, asset_key_prefix, docs_url=dbt_output.docs_url
        )
        if materialization is not None:
            yield materialization
