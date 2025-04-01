from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Callable, Optional, Union

import dateutil
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    MetadataValue,
    Output,
    _check as check,
)
from dagster._core.definitions.metadata import RawMetadataValue

from dagster_dbt.cloud.types import DbtCloudOutput
from dagster_dbt.utils import ASSET_RESOURCE_TYPES, default_node_info_to_asset_key


def _resource_type(unique_id: str) -> str:
    # returns the type of the node (e.g. model, test, snapshot)
    return unique_id.split(".")[0]


def _node_result_to_metadata(node_result: Mapping[str, Any]) -> Mapping[str, RawMetadataValue]:
    return {
        "Materialization Strategy": node_result["config"]["materialized"],
        "Database": node_result["database"],
        "Schema": node_result["schema"],
        "Alias": node_result["alias"],
        "Description": node_result["description"],
    }


def _timing_to_metadata(timings: Sequence[Mapping[str, Any]]) -> Mapping[str, RawMetadataValue]:
    metadata: dict[str, RawMetadataValue] = {}
    for timing in timings:
        if timing["name"] == "execute":
            desc = "Execution"
        elif timing["name"] == "compile":
            desc = "Compilation"
        else:
            continue

        # dateutil does not properly expose its modules to static checkers
        started_at = dateutil.parser.isoparse(timing["started_at"])  # type: ignore
        completed_at = dateutil.parser.isoparse(timing["completed_at"])  # type: ignore
        duration = completed_at - started_at
        metadata.update(
            {
                f"{desc} Started At": started_at.isoformat(timespec="seconds"),
                f"{desc} Completed At": started_at.isoformat(timespec="seconds"),
                f"{desc} Duration": duration.total_seconds(),
            }
        )
    return metadata


def result_to_events(
    result: Mapping[str, Any],
    docs_url: Optional[str] = None,
    node_info_to_asset_key: Optional[Callable[[Mapping[str, Any]], AssetKey]] = None,
    manifest_json: Optional[Mapping[str, Any]] = None,
    extra_metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    generate_asset_outputs: bool = False,
) -> Iterator[Union[AssetMaterialization, AssetObservation, Output]]:
    """This is a hacky solution that attempts to consolidate parsing many of the potential formats
    that dbt can provide its results in. This is known to work for CLI Outputs for dbt versions 0.18+,
    as well as RPC responses for a similar time period, but as the RPC response schema is not documented
    nor enforced, this can become out of date easily.
    """
    node_info_to_asset_key = check.opt_callable_param(
        node_info_to_asset_key, "node_info_to_asset_key", default=default_node_info_to_asset_key
    )

    # status comes from set of fields rather than "status"
    if "fail" in result:
        status = (
            "fail"
            if result.get("fail")
            else "skip"
            if result.get("skip")
            else "error"
            if result.get("error")
            else "success"
        )
    else:
        status = result["status"]

    # all versions represent timing the same way
    metadata = {"Status": status, "Execution Time (seconds)": result["execution_time"]}
    metadata.update(_timing_to_metadata(result["timing"]))

    # working with a response that contains the node block (RPC and CLI 0.18.x)
    if "node" in result:
        unique_id = result["node"]["unique_id"]
        metadata.update(_node_result_to_metadata(result["node"]))
    else:
        unique_id = result["unique_id"]

    if docs_url:
        metadata["docs_url"] = MetadataValue.url(f"{docs_url}#!/model/{unique_id}")

    if extra_metadata:
        metadata.update(extra_metadata)

    # if you have a manifest available, get the full node info, otherwise just populate unique_id
    dbt_resource_props = (
        manifest_json["nodes"][unique_id] if manifest_json else {"unique_id": unique_id}
    )

    node_resource_type = _resource_type(unique_id)

    if node_resource_type in ASSET_RESOURCE_TYPES and status == "success":
        if generate_asset_outputs:
            yield Output(
                value=None,
                output_name=node_info_to_asset_key(dbt_resource_props).to_python_identifier(),
                metadata=metadata,
            )
        else:
            yield AssetMaterialization(
                asset_key=node_info_to_asset_key(dbt_resource_props),
                description=f"dbt node: {unique_id}",
                metadata=metadata,
            )
    # can only associate tests with assets if we have manifest_json available
    elif node_resource_type == "test" and manifest_json and status != "skipped":
        upstream_unique_ids = manifest_json["nodes"][unique_id]["depends_on"]["nodes"]
        # tests can apply to multiple asset keys
        for upstream_id in upstream_unique_ids:
            # the upstream id can reference a node or a source
            dbt_resource_props = manifest_json["nodes"].get(upstream_id) or manifest_json[
                "sources"
            ].get(upstream_id)
            if dbt_resource_props is None:
                continue
            upstream_asset_key = node_info_to_asset_key(dbt_resource_props)
            yield AssetObservation(
                asset_key=upstream_asset_key,
                metadata={
                    "Test ID": result["unique_id"],
                    "Test Status": status,
                    "Test Message": result.get("message") or "",
                },
            )


def generate_events(
    dbt_output: DbtCloudOutput,
    node_info_to_asset_key: Optional[Callable[[Mapping[str, Any]], AssetKey]] = None,
    manifest_json: Optional[Mapping[str, Any]] = None,
) -> Iterator[Union[AssetMaterialization, AssetObservation]]:
    """This function yields :py:class:`dagster.AssetMaterialization` events for each model updated by
    a dbt command, and :py:class:`dagster.AssetObservation` events for each test run.

    Information parsed from a :py:class:`~DbtOutput` object.
    """
    for result in dbt_output.result["results"]:
        for event in result_to_events(
            result,
            docs_url=dbt_output.docs_url,
            node_info_to_asset_key=node_info_to_asset_key,
            manifest_json=manifest_json,
        ):
            yield check.inst(
                event,
                (AssetMaterialization, AssetObservation),
            )


def generate_materializations(
    dbt_output: DbtCloudOutput,
    asset_key_prefix: Optional[Sequence[str]] = None,
) -> Iterator[AssetMaterialization]:
    """This function yields :py:class:`dagster.AssetMaterialization` events for each model updated by
    a dbt command.
    """
    asset_key_prefix = check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    for event in generate_events(
        dbt_output,
        node_info_to_asset_key=lambda info: AssetKey(
            asset_key_prefix + info["unique_id"].split(".")
        ),
    ):
        yield check.inst(event, AssetMaterialization)
