from typing import Union

from dagster import ConfigurableResource
from deltalake import DeltaTable
from pydantic import Field

from .config import AzureConfig, GcsConfig, LocalConfig, S3Config


class DeltaTableResource(ConfigurableResource):
    """Resource for interacting with a Delta table.

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_deltalake import DeltaTableResource, LocalConfig

            @asset
            def my_table(delta_table: DeltaTableResource):
                df = delta_table.load().to_pandas()

            defs = Definitions(
                assets=[my_table],
                resources={
                    "delta_table": DeltaTableResource(
                        url="/path/to/table",
                        storage_options=LocalConfig()
                    )
                }
            )

    """

    url: str

    storage_options: Union[AzureConfig, S3Config, LocalConfig, GcsConfig] = Field(
        discriminator="provider"
    )

    def load(self) -> DeltaTable:
        options = self.storage_options.dict() if self.storage_options else {}
        table = DeltaTable(table_uri=self.url, storage_options=options)
        return table
