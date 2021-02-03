from typing import Iterator, List, Optional, Union

from dagster import AssetMaterialization, EventMetadataEntry, check

from .cli.types import DbtCliOutput
from .rpc.types import DbtRpcOutput


def generate_materializations(
    dbt_output: Union[DbtRpcOutput, DbtCliOutput], asset_key_prefix: Optional[List[str]] = None
) -> Iterator[AssetMaterialization]:
    """Yields ``AssetMaterializations`` for metadata in the dbt RPC ``DbtRpcOutput``."""

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    for node_result in dbt_output.result.results:
        if node_result.node["resource_type"] in ["model", "snapshot"]:
            success = not node_result.fail and not node_result.skip and not node_result.error
            if success:
                entries = [
                    EventMetadataEntry.json(data=node_result.node, label="Node"),
                    EventMetadataEntry.text(text=str(node_result.status), label="Status"),
                    EventMetadataEntry.float(
                        value=node_result.execution_time,
                        label="Execution Time (seconds)",
                    ),
                    EventMetadataEntry.text(
                        text=node_result.node["config"]["materialized"],
                        label="Materialization Strategy",
                    ),
                    EventMetadataEntry.text(text=node_result.node["database"], label="Database"),
                    EventMetadataEntry.text(text=node_result.node["schema"], label="Schema"),
                    EventMetadataEntry.text(text=node_result.node["alias"], label="Alias"),
                    EventMetadataEntry.text(
                        text=node_result.node["description"], label="Description"
                    ),
                ]
                for step_timing in node_result.step_timings:
                    if step_timing.name == "execute":
                        execution_entries = [
                            EventMetadataEntry.text(
                                text=step_timing.started_at.isoformat(timespec="seconds"),
                                label="Execution Started At",
                            ),
                            EventMetadataEntry.text(
                                text=step_timing.completed_at.isoformat(timespec="seconds"),
                                label="Execution Completed At",
                            ),
                            EventMetadataEntry.float(
                                # this is a value like datetime.timedelta(microseconds=51484)
                                value=step_timing.duration.total_seconds(),
                                label="Execution Duration",
                            ),
                        ]
                        entries.extend(execution_entries)
                    if step_timing.name == "compile":
                        execution_entries = [
                            EventMetadataEntry.text(
                                text=step_timing.started_at.isoformat(timespec="seconds"),
                                label="Compilation Started At",
                            ),
                            EventMetadataEntry.text(
                                text=step_timing.completed_at.isoformat(timespec="seconds"),
                                label="Compilation Completed At",
                            ),
                            EventMetadataEntry.float(
                                # this is a value like datetime.timedelta(microseconds=51484)
                                value=step_timing.duration.total_seconds(),
                                label="Compilation Duration",
                            ),
                        ]
                        entries.extend(execution_entries)

                unique_id = node_result.node["unique_id"]
                yield AssetMaterialization(
                    description="dbt node: {unique_id}".format(unique_id=unique_id),
                    metadata_entries=entries,
                    asset_key=asset_key_prefix + unique_id.split("."),
                )
