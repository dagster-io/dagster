from typing import Iterator, Union

from dagster import AssetMaterialization, EventMetadataEntry

from .cli.types import DbtCliOutput
from .rpc.types import DbtRpcOutput


def generate_materializations(
    dbt_output: Union[DbtRpcOutput, DbtCliOutput]
) -> Iterator[AssetMaterialization]:
    """Yields ``AssetMaterializations`` for metadata in the dbt RPC ``DbtRpcOutput``."""
    for node_result in dbt_output.result.results:
        if node_result.node["resource_type"] in ["model", "snapshot"]:
            success = not node_result.fail and not node_result.skip and not node_result.error
            if success:
                entries = [
                    EventMetadataEntry.json(data=node_result.node, label="Node"),
                    EventMetadataEntry.text(text=str(node_result.status), label="Status"),
                    EventMetadataEntry.text(
                        text=str(node_result.execution_time), label="Execution Time (seconds)"
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
                            EventMetadataEntry.text(
                                text=str(step_timing.duration), label="Execution Duration (seconds)"
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
                            EventMetadataEntry.text(
                                text=str(step_timing.duration),
                                label="Compilation Duration (seconds)",
                            ),
                        ]
                        entries.extend(execution_entries)

                yield AssetMaterialization(
                    description="A materialized node within the dbt graph.",
                    metadata_entries=entries,
                    asset_key=node_result.node["unique_id"],
                )
