from functools import cached_property
from typing import Annotated, Any, Optional, cast

import dagster as dg
import pydantic
from pyspark.sql import SparkSession


class SparkSessionComponent(dg.Component, dg.Model, dg.Resolvable):
    """Component which provides a spark session which can be used to execute code in Spark.

    Usage in Python:

    .. code-block:: python

        import dagster as dg
        from dagster_pyspark import SparkSessionComponent

        spark = (
            dg.ComponentTree.for_project(Path(__file__))
            .load_component_at_path("my_spark_session", as_type=SparkSessionComponent)
            .session
        )
        spark.sql("SELECT 1")

    """

    app_name: Optional[str] = None
    url: Annotated[
        Optional[str],
        pydantic.Field(
            description="The URL of the spark server to connect to. If not provided, the spark server will be inferred from the environment."
        ),
    ] = None
    config: Annotated[
        Optional[dict[str, Any]],
        pydantic.Field(
            description="Additional spark configuration options. See https://spark.apache.org/docs/latest/configuration.html#available-properties for more info."
        ),
    ] = None

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

    @cached_property
    def session(self) -> SparkSession:
        """Constructs a SparkSession matching the configuration set in this component."""
        builder = cast("SparkSession.Builder", SparkSession.builder)
        if self.app_name:
            builder = builder.appName(self.app_name)
        if self.url:
            builder = builder.remote(self.url)
        if self.config:
            for key, value in self.config.items():
                builder = builder.config(key, value)
        return builder.getOrCreate()
