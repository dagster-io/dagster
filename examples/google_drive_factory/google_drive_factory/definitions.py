import json
import os
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Union

import dagster as dg
import duckdb
import polars as pl
from dagster_duckdb import DuckDBResource
from google.oauth2 import service_account
from googleapiclient.discovery import build


@dataclass
class DriveFile:
    id: str
    name: str
    createdTime: str
    modifiedTime: str


def drop_create_duckdb_table(
    table_name: str, df: Union[pl.DataFrame, duckdb.DuckDBPyRelation]
) -> None:
    """Drop and recreate a table with the provided DataFrame or DuckDB relation data.

    Args:
        table_name: Name of the table to create
        df: Polars DataFrame or DuckDB relation containing the data
    """
    conn = None
    try:
        conn = duckdb.connect("db.duckdb")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        conn.commit()
    finally:
        if conn:
            conn.close()


def realtor_asset_factory(file_definition: DriveFile) -> dg.Definitions:
    file_name = file_definition.name[:-4]
    file_id = file_definition.id

    @dg.asset(
        name=file_name,
        group_name="ingestion",
        kinds={"polars", "duckdb", "google_drive"},
        description=f"Reads {file_name} from Google Drive folder and saves to duckdb database",
    )
    def read_csv_from_drive(
        context: dg.AssetExecutionContext, duckdb: DuckDBResource
    ) -> dg.MaterializeResult:
        context.log.info(f"Reading file {file_name} from Google Drive")
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        csv_string = content.decode("utf-8")
        df = pl.read_csv(StringIO(csv_string))
        drop_create_duckdb_table(file_name, df)

        return dg.MaterializeResult(
            metadata={
                "file_id": file_id,
                "file_name": file_name,
                "num_records": len(df),
            }
        )

    file_job = dg.define_asset_job(name=f"{file_name}_job", selection=[read_csv_from_drive])

    @dg.sensor(
        name=f"{file_name}_sensor",
        job_name=f"{file_name}_job",
        minimum_interval_seconds=15,
    )
    def file_sensor(context):
        # Get current modification time from cursor
        last_mtime = float(context.cursor) if context.cursor else 0

        # Get file details from Drive
        file_metadata = service.files().get(fileId=file_id, fields="modifiedTime").execute()

        current_mtime = datetime.strptime(
            file_metadata["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).timestamp()

        # If file has been modified, trigger the job
        if current_mtime > last_mtime:
            context.update_cursor(str(current_mtime))
            # Create AssetKey for the file
            asset_key = dg.AssetKey(file_name)
            yield dg.RunRequest(run_key=str(current_mtime), asset_selection=[asset_key])

    return dg.Definitions(
        assets=[read_csv_from_drive],
        jobs=[file_job],
        sensors=[file_sensor],
    )


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if json_str is None:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set")

# Parse JSON service account info
json_data = json.loads(json_str)

# Create credentials - using json_data, not folder ID
credentials = service_account.Credentials.from_service_account_info(
    json_data,
    scopes=SCOPES,  # Remove asterisks around scopes
)
service = build("drive", "v3", credentials=credentials)
folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

# Get files from folder
query = f"'{folder_id}' in parents and mimeType='text/csv'"
results = (
    service.files().list(q=query, fields="files(id, name, createdTime, modifiedTime)").execute()
)

realtor_definitions = [
    realtor_asset_factory(DriveFile(**file)) for file in results.get("files", [])
]

defs = dg.Definitions.merge(
    *realtor_definitions, dg.Definitions(resources={"duckdb": DuckDBResource(database="db.duckdb")})
)
