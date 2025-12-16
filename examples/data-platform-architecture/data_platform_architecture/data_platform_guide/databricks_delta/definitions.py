from dagster import Definitions, EnvVar

from data_platform_architecture.data_platform_guide.databricks_delta.defs.resources import (
    DatabricksResource,
    DeltaStorageResource,
)

definitions = Definitions(
    assets=[],
    resources={
        "databricks": DatabricksResource(
            server_hostname=EnvVar("DATABRICKS_SERVER_HOSTNAME").get_value() or "",
            http_path=EnvVar("DATABRICKS_HTTP_PATH").get_value() or "",
            token=EnvVar("DATABRICKS_TOKEN").get_value() or "",
            demo_mode=not bool(EnvVar("DATABRICKS_SERVER_HOSTNAME").get_value()),
        ),
        "delta_storage": DeltaStorageResource(
            storage_path=EnvVar("DELTA_STORAGE_PATH").get_value() or "data/delta",
            demo_mode=not bool(EnvVar("DELTA_STORAGE_PATH").get_value()),
        ),
    },
)
