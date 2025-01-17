from typing import Any

import dagster._check as check
from dagster import ConfigurableResource, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict
from pydantic import PrivateAttr
from pyspark.sql import SparkSession


def spark_session_from_config(spark_conf=None):
    spark_conf = check.opt_dict_param(spark_conf, "spark_conf")
    builder = SparkSession.builder
    flat = flatten_dict(spark_conf)
    for key, value in flat:
        builder = builder.config(key, value)  # pyright: ignore[reportAttributeAccessIssue]

    return builder.getOrCreate()  # pyright: ignore[reportAttributeAccessIssue]


class PySparkResource(ConfigurableResource):
    """This resource provides access to a PySpark Session for executing PySpark code within Dagster.

    Example:
        .. code-block:: python

            @op
            def my_op(pyspark: PySparkResource)
                spark_session = pyspark.spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")


            @job(
                resource_defs={
                    "pyspark": PySparkResource(
                        spark_config={
                            "spark.executor.memory": "2g"
                        }
                    )
                }
            )
            def my_spark_job():
                my_op()
    """

    spark_config: dict[str, Any]
    _spark_session = PrivateAttr(default=None)

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._spark_session = spark_session_from_config(self.spark_config)

    @property
    def spark_session(self) -> Any:
        return self._spark_session

    @property
    def spark_context(self) -> Any:
        return self.spark_session.sparkContext


@dagster_maintained_resource
@resource({"spark_conf": spark_config()})
def pyspark_resource(init_context) -> PySparkResource:
    """This resource provides access to a PySpark SparkSession for executing PySpark code within Dagster.

    Example:
        .. code-block:: python

            @op(required_resource_keys={"pyspark"})
            def my_op(context):
                spark_session = context.resources.pyspark.spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")

            my_pyspark_resource = pyspark_resource.configured(
                {"spark_conf": {"spark.executor.memory": "2g"}}
            )

            @job(resource_defs={"pyspark": my_pyspark_resource})
            def my_spark_job():
                my_op()
    """
    context_updated_config = init_context.replace_config(
        {"spark_config": init_context.resource_config["spark_conf"]}
    )
    return PySparkResource.from_resource_context(context_updated_config)


class LazyPySparkResource(ConfigurableResource):
    """This resource provides access to a lazily-created  PySpark SparkSession for executing PySpark
    code within Dagster, avoiding the creation of a SparkSession object until the .spark_session attribute
    of the resource is accessed. This is helpful for avoiding the creation (and startup penalty) of a SparkSession
    until it is actually needed / accessed by an op or IOManager.

    Example:
        .. code-block:: python

            @op
            def my_op(lazy_pyspark: LazyPySparkResource)
                spark_session = lazy_pyspark.spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")

            @job(
                resource_defs={
                    "lazy_pyspark": LazyPySparkResource(
                        spark_config={
                            "spark.executor.memory": "2g"
                        }
                    )
                }
            )
            def my_spark_job():
                my_op()
    """

    spark_config: dict[str, Any]
    _spark_session = PrivateAttr(default=None)

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _init_session(self) -> None:
        if self._spark_session is None:
            self._spark_session = spark_session_from_config(self.spark_config)

    @property
    def spark_session(self) -> Any:
        self._init_session()
        return check.not_none(self._spark_session)

    @property
    def spark_context(self) -> Any:
        self._init_session()
        return check.not_none(self._spark_session).sparkContext


@dagster_maintained_resource
@resource({"spark_conf": spark_config()})
def lazy_pyspark_resource(init_context: InitResourceContext) -> LazyPySparkResource:
    """This resource provides access to a lazily-created  PySpark SparkSession for executing PySpark
    code within Dagster, avoiding the creation of a SparkSession object until the .spark_session attribute
    of the resource is accessed. This is helpful for avoiding the creation (and startup penalty) of a SparkSession
    until it is actually needed / accessed by an op or IOManager.

    Example:
        .. code-block:: python

            @op(required_resource_keys={"lazy_pyspark"})
            def my_op(context):
                spark_session = context.resources.lazy_pyspark.spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")

            my_pyspark_resource = lazy_pyspark_resource.configured(
                {"spark_conf": {"spark.executor.memory": "2g"}}
            )

            @job(resource_defs={"lazy_pyspark": my_pyspark_resource})
            def my_spark_job():
                my_op()
    """
    context_updated_config = init_context.replace_config(
        {"spark_config": init_context.resource_config["spark_conf"]}
    )
    return LazyPySparkResource.from_resource_context(context_updated_config)
