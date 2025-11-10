from datetime import datetime, timedelta

from dagster_sharepoint import FileInfoConfig, SharePointResource

import dagster as dg


@dg.asset(compute_kind="sharepoint")
def process_sharepoint_file(
    context: dg.AssetExecutionContext,
    sharepoint: SharePointResource,
    config: FileInfoConfig,
):
    """Process SharePoint files."""
    context.log.info(f"Processing file from SharePoint {config}")

    # Download the file contents
    contents = sharepoint.download_file(config.id)
    context.log.info(f"Downloaded file {config.parent_path}/{config.name}")

    # Process file contents (example: count lines if it's a text file)
    if config.name.endswith(".csv"):
        lines = contents.decode("utf-8").splitlines()
        context.log.info(f"CSV file has {len(lines)} lines")
        return {"file_name": config.name, "lines": len(lines)}

    return {"file_name": config.name, "size": len(contents)}


@dg.sensor(
    name="sharepoint_new_files",
    minimum_interval_seconds=600,
    target=[process_sharepoint_file],
)
def sharepoint_new_files(
    context: dg.SensorEvaluationContext,
    sharepoint: SharePointResource,
) -> dg.SensorResult:
    """Sensor that checks for new or created files in SharePoint.

    This sensor:
    1. Checks a configured SharePoint folder for files created since the last run
    2. Triggers runs for each new file found
    3. Stores the last check timestamp in cursor storage
    """
    last_check = (
        datetime.fromisoformat(context.cursor)
        if context.cursor
        else datetime.now() - timedelta(weeks=999)
    )
    current_check = datetime.now()

    # Look for newly created CSV files
    newly_created_files = sharepoint.list_newly_created_files(
        since_timestamp=last_check,
        file_name_glob_pattern="*/Reports/*.csv",
        recursive=True,
    )

    if not newly_created_files:
        return dg.SkipReason(f"No new files found since {last_check.isoformat()}")

    # Create run requests for each new file
    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(
                asset_selection=[process_sharepoint_file.key],
                run_key=file.id,
                run_config=dg.RunConfig(
                    ops={
                        process_sharepoint_file.key.to_python_identifier(): {
                            "config": file.to_config_dict()
                        }
                    }
                ),
            )
            for file in newly_created_files
        ],
        cursor=current_check.isoformat(),
    )


defs = dg.Definitions(
    assets=[process_sharepoint_file],
    sensors=[sharepoint_new_files],
    resources={
        "sharepoint": SharePointResource(
            site_id=dg.EnvVar("SHAREPOINT_SITE_ID"),
            tenant_id=dg.EnvVar("AZURE_TENANT_ID"),
            client_id=dg.EnvVar("AZURE_CLIENT_ID"),
            client_secret=dg.EnvVar("AZURE_CLIENT_SECRET"),
        ),
    },
)
