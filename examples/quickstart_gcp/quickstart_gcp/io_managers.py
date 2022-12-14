import json

import pandas as pd
import pandas_gbq
from google.oauth2 import service_account

from dagster import (
    Field,
    IOManager,
    InitResourceContext,
    InputContext,
    OutputContext,
    StringSource,
    io_manager,
)

# Learn more about custom I/O managers in Dagster docs:
# https://docs.dagster.io/concepts/io-management/io-managers#a-custom-io-manager-that-stores-pandas-dataframes-in-tables


class BigQueryDataframeIOManager(IOManager):
    def __init__(self, credentials: dict, project_id: str, dataset_id: str) -> None:
        # `from_service_account_info` accepts a dictionary corresponding to the JSON file contents
        # If you'd like to refer to the JSON file path, change it to `from_service_account_file`
        self._credentials = service_account.Credentials.from_service_account_info(credentials)
        self._project_id = project_id
        self._dataset_id = dataset_id

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        # Skip handling if the output is None
        if obj is None:
            return

        table_name = context.asset_key.to_python_identifier()

        pandas_gbq.to_gbq(
            obj,
            f"{self._dataset_id}.{table_name}",
            project_id=self._project_id,
            credentials=self._credentials,
            if_exists="replace",  # always overwrite
        )

        # Recording metadata from an I/O manager:
        # https://docs.dagster.io/concepts/io-management/io-managers#recording-metadata-from-an-io-manager
        context.add_output_metadata({"dataset_id": self._dataset_id, "table_name": table_name})

    def load_input(self, context: InputContext):
        # upstream_output.asset_key is the asset key given to the Out that we're loading for
        table_name = context.upstream_output.asset_key.to_python_identifier()

        df = pandas_gbq.read_gbq(
            f"SELECT * FROM `{self._dataset_id}.{table_name}`", credentials=self._credentials
        )
        return df


@io_manager(
    config_schema={
        "credentials": StringSource,
        "project_id": StringSource,
        "dataset_id": Field(
            str, default_value="my_dataset", description="Dataset ID. Defaults to 'my_dataset'"
        ),
    }
)
def bigquery_pandas_io_manager(init_context: InitResourceContext) -> BigQueryDataframeIOManager:
    return BigQueryDataframeIOManager(
        credentials=json.loads(init_context.resource_config["credentials"]),
        project_id=init_context.resource_config["project_id"],
        dataset_id=init_context.resource_config["dataset_id"],
    )
