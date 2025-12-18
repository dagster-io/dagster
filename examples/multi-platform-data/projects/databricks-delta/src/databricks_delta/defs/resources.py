import os

import pandas as pd
from dagster import ConfigurableResource


class DatabricksResource(ConfigurableResource):
    server_hostname: str = ""
    http_path: str = ""
    token: str = ""
    demo_mode: bool = False

    def query(self, sql: str) -> pd.DataFrame:
        if self.demo_mode:
            return pd.DataFrame()
        return pd.DataFrame()


class DeltaStorageResource(ConfigurableResource):
    storage_path: str
    demo_mode: bool = False

    def write_delta_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        mode: str = "overwrite",
    ) -> str:
        if self.demo_mode:
            return f"{self.storage_path}/{table_name}"
        return f"{self.storage_path}/{table_name}"

    def read_delta_table(self, table_name: str) -> pd.DataFrame:
        if self.demo_mode:
            return pd.DataFrame()
        return pd.DataFrame()


databricks_resource = DatabricksResource(
    server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", ""),
    http_path=os.getenv("DATABRICKS_HTTP_PATH", ""),
    token=os.getenv("DATABRICKS_TOKEN", ""),
    demo_mode=not bool(os.getenv("DATABRICKS_SERVER_HOSTNAME")),
)

delta_storage_resource = DeltaStorageResource(
    storage_path=os.getenv("DELTA_STORAGE_PATH", "data/delta"),
    demo_mode=not bool(os.getenv("DELTA_STORAGE_PATH")),
)
