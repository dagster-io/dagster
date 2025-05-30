from functools import reduce
from typing import Any, Optional

import dlt
from dagster import Config
from dlt.common.configuration.providers import CustomLoaderDocProvider


def dlt_config(
    config_cls: Optional[type[Config]] = None,
    *,
    section: Optional[str] = None,
    **model_dump_kwargs: Any,
):
    """Decorator to wrap a Dagster Config class to be used as a DLT configuration provider.

    Args:
        section (Optional[str]): The section name to insert your configuration under in the DLT config. Will be stored at root level if not provided.
        **model_dump_kwargs: Additional keyword arguments to pass to the model_dump method.

    Examples:
        .. code-block:: python

            from dagster_dlt import dlt_assets
            from pydantic import Field
            import dlt
            from dagster import Config, AssetExecutionContext


            # Using sections to organize configs
            @dlt_config(section="sources.postgres")
            class PostgresSourceConfig(Config):
                schema_name: str = "public"
                table_name: str = "users"
                incremental_field: Optional[str] = None

            # Complete pipeline example
            @dlt.source(section="postgres")
            def postgres_source(
                schema_name: str = dlt.config.value,
                table_name: str = dlt.config.value,
                incremental_field: Optional[str] = dlt.config.value
            ):
                @dlt.resource
                def load_table(table_name: str):
                    query = f"SELECT * FROM {schema_name}.{table_name}"
                    if incremental_field:
                        query += f" WHERE {incremental_field} > :last_value"
                    yield from run_query(query)
                # Create resources for each table
                return load_table(table_name)

            @dlt_assets(
                dlt_source=postgres_source,
                dlt_pipeline=dlt.pipeline()
            )
            def assets(context: AssetExecutionContext, dlt: DagsterDltResource, config: PostgresSourceConfig):
                yield from dlt.run(context=context)



            # Using model_dump_kwargs to control serialization
            @dlt_config(section="api.endpoints", by_alias=True, exclude_defaults=True)
            class APIConfig(Config):
                base_url: str = Field(alias="baseUrl")
                api_key: str = Field(alias="apiKey")
                timeout: int = 30  # Won't be included in DLT config unless explicitly set due to exclude_defaults=True

            @dlt.source
            def my_api():
                # Access aliased config values with dot notation
                base_url = dlt.config["api.endpoints.baseUrl"]
                api_key = dlt.config["api.endpoints.apiKey"]

                headers = {"Authorization": f"Bearer {api_key}"}

                @dlt.resource
                def fetch_data():
                    response = requests.get(base_url, headers=headers)
                    yield from response.json()

                return fetch_data()

    """

    def create_wrapped_config(cls: type[Config]) -> type[Config]:
        """Helper to create the wrapped config class."""
        class DagsterDltConfigWrapper(cls):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self._provider = CustomLoaderDocProvider(
                    name=cls.__name__,
                    loader=self._dlt_config_loader
                )

                dlt.config.register_provider(self._provider)

            def _dlt_config_loader(self) -> dict:
                config_dict = self.model_dump(**model_dump_kwargs)

                if section:
                    return reduce(lambda d, key: {key: d}, reversed(section.split('.')), config_dict)
                else:
                    return config_dict

        DagsterDltConfigWrapper.__name__ = cls.__name__
        DagsterDltConfigWrapper.__qualname__ = cls.__qualname__
        DagsterDltConfigWrapper.__module__ = cls.__module__
        return DagsterDltConfigWrapper

    def inner(cls: type[Config]) -> type[Config]:
        return create_wrapped_config(cls)

    return create_wrapped_config(config_cls) if config_cls else inner
