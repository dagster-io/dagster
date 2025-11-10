import tempfile
from datetime import datetime

from dagster_sftp import SFTPFileInfoConfig, SFTPResource

import dagster as dg


@dg.asset(compute_kind="sftp")
def process_sftp_file(
    context: dg.AssetExecutionContext, config: SFTPFileInfoConfig, sftp: SFTPResource
):
    """Process a file from SFTP server."""
    context.log.info(f"Processing file {config.path}")

    # Download the file to a temporary location
    with tempfile.NamedTemporaryFile() as tmp_file:
        sftp.get_file(config.path, tmp_file.name)

        # Process the file (example: read contents)
        with open(tmp_file.name) as f:
            lines = f.readlines()
            context.log.info(f"Processed file with {len(lines)} lines")

    return {"file_processed": config.path, "lines": len(lines)}


@dg.sensor(name="sftp_file_sensor", target=process_sftp_file)
def sftp_file_sensor(context: dg.SensorEvaluationContext, sftp: SFTPResource):
    """Detect new files on SFTP server and trigger processing."""
    last_check = datetime.fromisoformat(context.cursor) if context.cursor else None
    current_check = datetime.now()

    # Look for new CSV files
    new_files = sftp.list_files(
        base_path="/incoming",
        pattern="*.csv",
        files_only=True,
        modified_after=last_check,
    )

    if not new_files:
        return dg.SkipReason(
            f"No new files found since {last_check.isoformat() if last_check else 'start'}"
        )

    # Create run requests for each new file
    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(
                asset_selection=[process_sftp_file.key],
                run_key=file.id,
                run_config=dg.RunConfig(
                    ops={
                        process_sftp_file.key.to_python_identifier(): {
                            "config": file.to_config_dict()
                        }
                    }
                ),
            )
            for file in new_files
        ],
        cursor=current_check.isoformat(),
    )


defs = dg.Definitions(
    assets=[process_sftp_file],
    sensors=[sftp_file_sensor],
    resources={
        "sftp": SFTPResource(
            host=dg.EnvVar("SFTP_HOST"),
            username=dg.EnvVar("SFTP_USERNAME"),
            password=dg.EnvVar("SFTP_PASSWORD"),
            port=22,
        ),
    },
)
