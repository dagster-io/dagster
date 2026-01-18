import json
import os
from datetime import datetime
from io import StringIO

import dagster as dg
import polars as pl
from dagster_duckdb import DuckDBResource
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pydantic import BaseModel, PrivateAttr


class DriveFile(BaseModel):
    id: str
    name: str
    createdTime: str
    modifiedTime: str


class GoogleDriveClient:
    """Handles the Google Drive client creation and API interactions."""

    def __init__(self, credentials_json: dict):
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)

    def retrieve_files(self, folder_id: str):
        """Query for files in a Google Drive folder."""
        query = f"'{folder_id}' in parents and mimeType='text/csv'"
        return (
            self.service.files()
            .list(q=query, fields="files(id, name, createdTime, modifiedTime)")
            .execute()
        )

    def request_content(self, file_id: str):
        """Fetch file content from Google Drive using file_id."""
        request = self.service.files().get_media(fileId=file_id)
        return request.execute()

    def get_file_metadata(self, file_id: str, fields: str = "modifiedTime"):
        """Get metadata for a specific file."""
        return self.service.files().get(fileId=file_id, fields=fields).execute()


class GoogleDriveResource(dg.ConfigurableResource):
    """Resource configuration for Google Drive credentials."""

    json_data: str

    _client: GoogleDriveClient = PrivateAttr()

    def setup_for_execution(self, context: dg.InitResourceContext):
        """Initialize the Google Drive client using the credentials."""
        credentials_json = json.loads(self.json_data)
        self._client = GoogleDriveClient(credentials_json)

    def retrieve_files(self, folder_id: str):
        """Delegates to the client to retrieve files."""
        return self._client.retrieve_files(folder_id)

    def request_content(self, file_id: str):
        """Delegates to the client to fetch content."""
        return self._client.request_content(file_id)

    def get_file_metadata(self, file_id: str, fields: str = "modifiedTime"):
        """Delegates to the client to get file metadata."""
        return self._client.get_file_metadata(file_id, fields)


def realtor_asset_factory(
    file_definition: DriveFile, google_drive: GoogleDriveResource
) -> dg.Definitions:
    file_name, _ = os.path.splitext(file_definition.name)
    file_id = file_definition.id

    @dg.asset(
        name=file_name,
        group_name="ingestion",
        kinds={"polars", "duckdb", "google_drive"},
        description=f"Reads {file_name} from Google Drive folder and saves to duckdb database",
    )
    def read_csv_from_drive(
        context: dg.AssetExecutionContext, duckdb: DuckDBResource, google_drive: GoogleDriveResource
    ) -> dg.MaterializeResult:
        context.log.info(f"Reading file {file_name} from Google Drive")
        request = google_drive.request_content(file_id)
        csv_string = request.decode("utf-8")
        df = pl.read_csv(StringIO(csv_string))

        with duckdb.get_connection() as conn:
            conn.execute(f"CREATE OR REPLACE TABLE {file_name} AS SELECT * FROM df")

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
    def file_sensor(context, google_drive: GoogleDriveResource):
        # Get current modification time from cursor
        last_mtime = float(context.cursor) if context.cursor else 0

        # Get file details from Drive
        file_metadata = google_drive.get_file_metadata(file_id)

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
        resources={"google_drive": google_drive, "duckdb": DuckDBResource(database="db.duckdb")},
    )


google_drive_resource = GoogleDriveResource(json_data=os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

google_drive_resource.setup_for_execution(dg.build_init_resource_context())

# Fetch files from the Google Drive folder using properly initialized _client
folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
file_results = google_drive_resource.retrieve_files(folder_id).get("files", [])

# Create realtor definitions dynamically
realtor_definitions = [
    realtor_asset_factory(DriveFile(**file), google_drive_resource) for file in file_results
]

defs = dg.Definitions.merge(
    *realtor_definitions, dg.Definitions(resources={"duckdb": DuckDBResource(database="db.duckdb")})
)
