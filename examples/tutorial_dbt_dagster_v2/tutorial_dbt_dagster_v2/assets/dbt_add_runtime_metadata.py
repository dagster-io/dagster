from dagster import OpExecutionContext, Output
from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest
from dateutil import parser

from tutorial_dbt_dagster_v2.assets import raw_manifest

## Case 7: Add detailed runtime metadata to the outputs. This replaces:
##   - runtime_metadata_fn

manifest: DbtManifest = DbtManifest(raw_manifest=raw_manifest)


@dbt_multi_asset(manifest=manifest)
def dbt_assets(context: OpExecutionContext, dbt: DbtClientV2):
    for event in dbt.cli(["build"]).stream():
        for dagster_event in event.to_default_asset_events(manifest=manifest):
            if isinstance(dagster_event, Output):
                event_node_info = event.event["data"]["node_info"]

                started_at = parser.isoparse(event_node_info["node_started_at"])
                completed_at = parser.isoparse(event_node_info["node_finished_at"])

                metadata = {
                    "Execution Started At": started_at.isoformat(timespec="seconds"),
                    "Execution Completed At": completed_at.isoformat(timespec="seconds"),
                    "Execution Duration": (completed_at - started_at).total_seconds(),
                }

                context.add_output_metadata(
                    metadata=metadata,
                    output_name=dagster_event.output_name,
                )

            yield dagster_event
