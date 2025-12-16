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
